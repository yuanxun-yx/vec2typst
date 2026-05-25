from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin
from typing import overload


@dataclass(frozen=True)
class Affine2D:
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    @overload
    def __matmul__(self, other: Affine2D) -> Affine2D: ...

    @overload
    def __matmul__(
        self,
        other: tuple[float, float],
    ) -> tuple[float, float]: ...

    def __matmul__(
        self,
        other: Affine2D | tuple[float, float],
    ) -> Affine2D | tuple[float, float]:

        if isinstance(other, Affine2D):
            return Affine2D(
                a=self.a * other.a + self.c * other.b,
                b=self.b * other.a + self.d * other.b,
                c=self.a * other.c + self.c * other.d,
                d=self.b * other.c + self.d * other.d,
                e=self.a * other.e + self.c * other.f + self.e,
                f=self.b * other.e + self.d * other.f + self.f,
            )
        elif isinstance(other, tuple):
            x, y = other
            return (
                self.a * x + self.c * y + self.e,
                self.b * x + self.d * y + self.f,
            )
        else:
            raise TypeError(f"invalid type {type(other)}")

    @property
    def angle(self) -> float:
        return degrees(atan2(self.b, self.a))


def translate(tx: float, ty: float = 0.0) -> Affine2D:
    return Affine2D(e=tx, f=ty)


def rotate(angle: float, cx: float = 0.0, cy: float = 0.0) -> Affine2D:
    r = radians(angle)
    rot = Affine2D(
        a=cos(r),
        b=sin(r),
        c=-sin(r),
        d=cos(r),
    )
    if cx == 0.0 and cy == 0.0:
        return rot
    return translate(cx, cy) @ rot @ translate(-cx, -cy)
