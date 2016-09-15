from dolfin import *
import numpy as np
from structur_sympy import *
set_log_active(False)
def solver_structure(N,dt):
    mesh = UnitSquareMesh(N,N)
    mesh2 = UnitSquareMesh(100,100)
    V = VectorFunctionSpace(mesh,"CG",1)
    V2 = VectorFunctionSpace(mesh2,"CG",2)

    psi = TestFunction(V)
    u = Function(V)
    #u0 = Function(V)
    #u1 = Function(V)
    class On(SubDomain):
    	def inside(self, x, on_boundary):
    		return on_boundary
    on = On()
    boundaries = FacetFunction("size_t",mesh)
    boundaries.set_all(0)
    on.mark(boundaries,1)
    u_0 = Expression(("x[0]*x[0]","x[1]*x[1]"))
    bc1 = DirichletBC(V,u_0, boundaries,1)
    bcs = [bc1]
    #plot(boundaries,interactive=True)

    mu_s = 0.5E6
    nu_s = 0.4
    rho_s = 1.0E3
    lamda = nu_s*2*mu_s/(1-2*nu_s)

    I_1,f = find_my_f()

    #    print I_1, f

    #I_1 = Expression(("x[0]*x[0]+t*t","x[1]*x[1]+t*t"),t=0)
    u1=interpolate(I_1,V)
    I_1.t = dt
    u0 = interpolate(I_1,V)


    k = Constant(dt)

    def s_s_n_l(U):
        I = Identity(2)
        F = I + grad(U)
        E = 0.5*((F.T*F)-I)
        return F*(lamda*tr(E)*I + 2*mu_s*E)

    G =rho_s*((1./k**2)*inner(u - 2*u0 + u1,psi))*dx + inner(s_s_n_l(0.5*(u+u0)),grad(psi))*dx - inner(f,psi)*dx

    T = 1.0
    t=2*dt
    counter = 0
    e_list = []
    while t<=T:
        I_1.t = t
        u_ = interpolate(I_1,V2)
        #plot(u_)
        f.t = t
        print "Timestep: ",t
        solve(G==0,u,bcs,solver_parameters={"newton_solver": \
        {"relative_tolerance": 1E-6,"absolute_tolerance":1E-6,"maximum_iterations":100,"relaxation_parameter":1.0}})
        #plot(u)
        u_new = interpolate(u,V2)
        e_list.append(errornorm(u_, u_new, norm_type="l2",degree_rise=3))

        u0.assign(u1)
        u1.assign(u)
        #print e_list[counter]
        t += dt
        counter += 1
    return np.mean(e_list), mesh.hmin()


#solver_structure(200)



N_list = [2,4,8,16,32]
E = np.zeros(len(N_list))
h = np.zeros(len(N_list))
for j in range(len(N_list)):
    E[j],h[j]=solver_structure(N_list[j],dt=0.1)
    print "Error: %2.2E ,N: %.d: "%(E[j],N_list[j])
for i in range(1, len(E)):
    r = np.log(E[i]/E[i-1])/np.log(h[i]/h[i-1])
    print "h=%10.2E r=%.6f" % (h[i], r)
