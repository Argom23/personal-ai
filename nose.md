Sí bro. El teorema de la Sec. 22 básicamente nos permite verificar que una función es analítica si las derivadas parciales de \(u\) y \(v\) son continuas y satisfacen Cauchy-Riemann:

\[
u_x=v_y,
\qquad
u_y=-v_x.
\]

Como queremos demostrar que son **entire**, estas condiciones deben cumplirse para todo \((x,y)\in\mathbb R^2\).

### (a)

\[
f(z)=3x+y+i(3y-x).
\]

Entonces

\[
u(x,y)=3x+y,
\qquad
v(x,y)=3y-x.
\]

Calculamos:

\[
u_x=3,
\qquad
u_y=1,
\]

\[
v_x=-1,
\qquad
v_y=3.
\]

Comprobamos Cauchy-Riemann:

\[
u_x=v_y
\]

porque

\[
3=3,
\]

y

\[
u_y=-v_x
\]

porque

\[
1=-(-1)=1.
\]

Las derivadas parciales son continuas en todo el plano, por lo tanto

\[
\boxed{f(z)\text{ es entire}.}
\]

De hecho,

\[
f'(z)=u_x+iv_x=3-i.
\]

---

### (b)

\[
f(z)=\sin x\cosh y+i\cos x\sinh y.
\]

Tenemos

\[
u(x,y)=\sin x\cosh y,
\]

\[
v(x,y)=\cos x\sinh y.
\]

Derivamos:

\[
u_x=\cos x\cosh y,
\]

\[
u_y=\sin x\sinh y,
\]

\[
v_x=-\sin x\sinh y,
\]

\[
v_y=\cos x\cosh y.
\]

Entonces

\[
u_x=v_y
\]

y

\[
u_y=-v_x.
\]

Como todas estas derivadas son continuas para todo \(x,y\),

\[
\boxed{f(z)\text{ es entire}.}
\]

Además,

\[
f'(z)
=
\cos x\cosh y-i\sin x\sinh y.
\]

Esto corresponde a

\[
\boxed{f'(z)=\cos z}.
\]

---

### (c)

\[
f(z)=e^{-y}\sin x-i e^{-y}\cos x.
\]

Entonces

\[
u(x,y)=e^{-y}\sin x,
\]

\[
v(x,y)=-e^{-y}\cos x.
\]

Derivamos:

\[
u_x=e^{-y}\cos x,
\]

\[
u_y=-e^{-y}\sin x,
\]

\[
v_x=e^{-y}\sin x,
\]

\[
v_y=e^{-y}\cos x.
\]

Comprobamos:

\[
u_x=v_y,
\]

porque ambos son

\[
e^{-y}\cos x,
\]

y

\[
u_y=-v_x,
\]

porque

\[
-e^{-y}\sin x=-e^{-y}\sin x.
\]

Todas las derivadas parciales son continuas en todo el plano, entonces

\[
\boxed{f(z)\text{ es entire}.}
\]

---

### (d)

\[
f(z)=(z^2-2)e^{-x}e^{-iy}.
\]

Primero observamos que

\[
e^{-x}e^{-iy}
=
e^{-(x+iy)}
=
e^{-z}.
\]

Por lo tanto,

\[
f(z)=(z^2-2)e^{-z}.
\]

Ahora, \(z^2-2\) es un polinomio, por lo que es entire, y \(e^{-z}\) también es entire.

El producto de dos funciones entire también es entire. Entonces

\[
\boxed{f(z)\text{ es entire}.}
\]

Si además ocupás la derivada:

\[
f'(z)
=
2ze^{-z}-(z^2-2)e^{-z},
\]

por lo que

\[
\boxed{
f'(z)=e^{-z}(2z-z^2+2)
}.
\]

En resumen, **las cuatro funciones son entire**.