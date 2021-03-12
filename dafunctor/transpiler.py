from collections import OrderedDict
from .common import *
from .expression import *
import re

class CFG():
    def __init__(self, target, parent=None, data=None):
        self.target = target
        self.parent = parent
        if parent is None:
            self.depth = -1
        else:
            self.depth = parent.depth + 1
        self.data = data
        if self.data is None:
            self.data = OrderedDict()
        self.stmt = []
        self.output = False

    def __repr__(self):
        return str(self.stmt)

    def __str__(self):
        return self.__repr__()

    def append(self, stmt):
        self.stmt.append(stmt)

    def enter(self):
        scope = CFG(self.target, parent=self, data=self.data)
        self.append(["scope", scope])
        return scope

    def print(self):
        import pprint
        pp = pprint.PrettyPrinter()
        pp.pprint(self.stmt)

def split_graph(functor):
    ret = []
    if functor.daf_is_joiner():
        for f in functor.subs:
            f._daf_requested_contiguous = True
            if not f._daf_is_contiguous:
                ret.append(f)
    else:
        for f in functor.subs:
            ret.extend(split_graph(f))
    if functor._daf_requested_contiguous and not functor._daf_is_contiguous:
        ret.append(functor)
    return ret

def build_cfg(ctx, path):
    value = None
    scope = ctx
    idepth = 0
    rg, phases = path
    for depth, (functor, sidx) in enumerate(phases):
        if depth == 0:
            out = phases[-1][0]
            if not out._daf_is_output and not out._daf_is_declared:
                out._daf_is_declared = True
                scope.append(["autobuf", out])
            scope.append(["for_shape", rg, scope.depth + 1, idepth])
            scope = scope.enter()

        if functor.partitions:
            if functor.iexpr:
                scope.append(["comment", functor.opdesc])
                for d,iexpr in enumerate(functor.iexpr):
                    scope.append(["val","i", ["idx", d, scope.depth, idepth+1], build_ast(scope, Expr(iexpr), sidx, functor.subs[sidx], idepth, value)])
                idepth += 1
        else:
            if functor.iexpr:
                scope.append(["comment", functor.opdesc])
                for d,iexpr in enumerate(functor.iexpr):
                    scope.append(["val", "i", ["idx", d, scope.depth, idepth+1], build_ast(scope, Expr(iexpr), sidx, functor.subs[sidx], idepth, value)])
                idepth += 1
            value = build_ast(scope, Expr(functor.vexpr), sidx, functor, idepth, value)

        output = False

        final_out = depth + 1 == len(phases)
        if not functor.sexpr is None: # scatter
            val = ["v", scope.depth]
            scope.append(["val", phases[-1][0].get_type(), val, value])
            scope.append(["for_scatter", functor.shape, functor.sexpr, scope.depth + 1, idepth])
            scope = scope.enter()
            value = val
        if final_out:
            if value is None:
                print("Path", path)
                raise AssertionError("value is None")
            scope.append(["=", functor, value, idepth, scope.depth])

def build_ast(ctx, expr, sidx, functor, depth, value):
    op = expr.op
    if type(op) in (int, float):
        return op
    elif op in ("+","-","*","//","/","%"):
        args = [build_ast(ctx, e, sidx, functor, depth, value) for e in expr]
        return [op, args]
    elif op == "ref":
        ref_a = build_ast(ctx, expr[0], sidx, functor, depth, value)
        ref_b = build_ast(ctx, expr[1], sidx, functor, depth, value)
        if type(ref_b) is list:
            ref_b = tuple(ref_b)
        return ["ref", ref_a, ref_b]
    elif op == "si":
        return sidx
    elif op == "d":
        name = functor.data.get_name()
        ctx.data[name] = (functor.data.get_type(), functor.data)
        return name
    elif re.match("-?[0-9]+", op):
        return ["term",op]
    elif re.match("d[0-9]+", op):
        i = int(op[1:])
        return ["term", functor.data[i]]
    elif re.match("i[0-9]+", op):
        return ["idx", int(op[1:]), ctx.depth, depth]
    elif re.match("v[0-9]+", op):
        i = int(op[1:])
        s = functor.subs[i]
        if functor._daf_exported:
            axis = []
            for i in rangel(functor.shape):
                axis.append(["*", [f"i{i}"]+[s for s in functor.shape[i+1:]]])
            return ["ref", functor.get_name(), ["+", axis]]
        elif not s.vexpr is None:
            return build_ast(ctx, Expr(s.vexpr), i, s, depth, value)
        else:
            return value
    elif op == "buf":
        buf_idx = build_ast(ctx, expr[0], sidx, functor, depth, value)
        return ["ref", functor.name, buf_idx]
    else:
        raise NotImplementedError("Invalid token {}".format(op))

def tailor_shape(paths):
    ret = []
    for path in paths:
        brg = path[0]
        phases = path[1]
        bfunctor, bsidx = phases[0]
        vs = [set() for i in rangel(bfunctor.shape)]

        for idx in ranger(brg):
            cidx = idx
            in_range = True

            if bfunctor.partitions:
                raise ValueError(f"Partitioned root functor {bfunctor}")
            else:
                pidx = bfunctor.eval_index(idx)

            if pidx is None:
                continue

            idx = pidx

            for functor, sidx in phases[1:]:
                if functor.partitions:
                    sfunctor = functor.subs[sidx]
                    srg = functor.partitions[sidx]
                    if len(idx) != len(srg):
                        raise AssertionError(f"Dimension mismatch {idx} {srg}")
                    if not all([i>=r[0] for i,r in zip(idx, srg)]):
                        in_range = False
                        break
                    if not all([i<r[0]+r[1]*r[2] for i,r in zip(idx, srg)]):
                        in_range = False
                        break
                    if not all([(i-r[0]) % r[2] == 0 for i,r in zip(idx, srg)]):
                        in_range = False
                        break

                pidx = functor.eval_index(idx, sidx)

                if pidx is None:
                    in_range = False
                    break

                idx = pidx

            if in_range:
                for i,c in enumerate(cidx):
                    vs[i].add(c)

        # slices generation
        vs = [sorted(list(v)) for v in vs]
        num = [len(v) for v in vs]
        if all([n > 0 for n in num]):
            base = [min(v) for v in vs]
            step = [v[1]-v[0] if len(v) > 1 else 1 for v in vs]
            rg = list(zip(base, num, step))
            ret.append((rg, phases))
    return ret

def build_blocks(functor, target):
    paths = []
    rg = functor.shape.shape

    if functor is target or not functor.daf_is_contiguous():
        if functor.partitions:
            for i,_ in enumerate(functor.partitions):
                for brg,bpath in build_blocks(functor.subs[i], target):
                    paths.append((brg, bpath+[(functor, i)]))
        elif not functor.daf_is_joiner():
            for i in rangel(functor.subs):
                for brg,bpath in build_blocks(functor.subs[i], target):
                    paths.append((brg, bpath+[(functor, i)]))

    if not paths:
        paths.append((rg, [(functor, 0)]))

    return paths