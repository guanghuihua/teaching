"""第一课数学例子的精确复算；运行需要 Python 与 sympy。

雅可比映射据 Tao 2026-07-21 正文公式(1)，详见前沿数学核查记录.md。
这段代码核验显式恒等式与课堂列举，不核验单位距离研究证明或NS论文。
"""
from itertools import combinations
import sympy as s

x, y, z = s.symbols('x y z')
F = s.Matrix([
    (1+x*y)**3*z + y**2*(1+x*y)*(4+3*x*y),
    y + 3*x*(1+x*y)**2*z + 3*x*y**2*(4+3*x*y),
    2*x - 3*x**2*y - x**3*z,
])
assert s.factor(F.jacobian([x, y, z]).det()) == -2
points = [(0, 0, -s.Rational(1, 4)),
          (1, -s.Rational(3, 2), s.Rational(13, 2)),
          (-1, s.Rational(3, 2), s.Rational(13, 2))]
for point in points:
    assert list(F.subs(dict(zip([x, y, z], point)))) == [-s.Rational(1, 4), 0, 0]

def unit_pairs(points):
    return [(a, b) for a, b in combinations(points, 2)
            if s.simplify(sum((u-v)**2 for u, v in zip(a, b))) == 1]

assert len(unit_pairs([(0, 0), (1, 0), (1, 1), (0, 1)])) == 4
assert len(unit_pairs([(0, 0), (1, 0), (s.Rational(1, 2), s.sqrt(3)/2),
                      (s.Rational(1, 2), -s.sqrt(3)/2)])) == 5
A = [1, 2, 5, 6, 7, 8]
answer1 = {c for k in range(1, 7) for c in combinations(A, k) if sum(c) == 8}
assert answer1 == {(8,), (1, 7), (2, 6), (1, 2, 5)}
answer2 = {c for c in combinations([3, 4, 5, 9, 10, 11], 3) if sum(c) % 12 == 0}
assert answer2 == {(3, 4, 5), (3, 10, 11), (4, 9, 11), (5, 9, 10)}
print('通过：雅可比行列式恒等式、三个输入的碰撞、两幅单位距离图及集合题前两问。')
