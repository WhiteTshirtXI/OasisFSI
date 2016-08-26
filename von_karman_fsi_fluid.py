from dolfin import *
import numpy as np

mesh = Mesh("von_karman_street_FSI_fluid.xml")
#plot(mesh,interactive=True)

V1 = VectorFunctionSpace(mesh, "CG", 2) # Fluid velocity
V2 = VectorFunctionSpace(mesh, "CG", 1) # Mesh movement
Q  = FunctionSpace(mesh, "CG", 1)       # Fluid Pressure

VVQ = MixedFunctionSpace([V1,Q])

# BOUNDARIES

Inlet = AutoSubDomain(lambda x: "on_boundary" and near(x[0],0))
Outlet = AutoSubDomain(lambda x: "on_boundary" and near(x[0],2.5))
Up = AutoSubDomain(lambda x: "on_boundary" and near(x[1],0.41))
Down = AutoSubDomain(lambda x: "on_boundary" and near(x[1],0))
#Circle = AutoSubDomain(lambda x: "on_boundary" and not (near(x[0],0) or near(x[0],2.2) or near(x[1],0) or near(x[1],0.41)))
class Circle(SubDomain):
	def inside(self, x, on_boundary):
		return on_boundary and not (near(x[0],0) or near(x[0],2.5) or near(x[1],0) or near(x[1],0.41))



#Bar = AutoSubDomain(lambda x: "on_boundary" and (near(x[1], 0.21)) or near(x[1], 0.19) or near(x[0], 0.6 ) )
#Circle =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  ))
#BarLeftSide =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  and x[1]>=0.19 and x[1]<=0.21 and x[0]>0.2 ))
#Circle_and_Bar = AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  ) or \
#(near(x[1], 0.21)) or near(x[1], 0.19) or near(x[0], 0.6 ))
test = DomainBoundary()
circle=Circle()
boundaries = FacetFunction("size_t",mesh)
boundaries.set_all(0)
circle.mark(boundaries, 1)
Inlet.mark(boundaries, 2)
Outlet.mark(boundaries, 3)
Up.mark(boundaries,4)
Down.mark(boundaries,5)



ds = Measure("ds", subdomain_data = boundaries)
dS = Measure("dS", subdomain_data = boundaries)
n = FacetNormal(mesh)
plot(boundaries,interactive=True)



#BOUNDARY CONDITIONS

Um = 0.2
H = 0.41
U_mean = 2.0*Um/3.0
inlet = Expression(("1.5*Um*x[1]*(H-x[1])/pow(H/2.0,2)","0"),t=0.0,Um = Um,H=H)
#inlet= Expression(("4.0*Um*x[1]*(H-x[1])/pow(H,2)","0"),t=0.0,Um = Um,H=H)

u_inlet = DirichletBC(VVQ.sub(0), (inlet), boundaries, 2)
p_0 = DirichletBC(VVQ.sub(1), Constant(0.0), boundaries,3)
nos = DirichletBC(VVQ.sub(0), ((0, 0)), boundaries, 1)
down = DirichletBC(VVQ.sub(0), ((0, 0)), boundaries, 4)
up = DirichletBC(VVQ.sub(0), ((0, 0)), boundaries, 5)

bcs = [nos,u_inlet, down, up,p_0]#,bc1]

# AREAS

#Bar_area = AutoSubDomain(lambda x: (0.19 <= x[1] <= 0.21) and 0.24<= x[0] <= 0.6) # only the "flag" or "bar"

#domains = CellFunction("size_t",mesh)
##domains.set_all(1)
#Bar_area.mark(domains,2)
#dx = Measure("dx",subdomain_data=domains)
#plot(domains,interactive = True)


# TEST TRIAL FUNCTIONS
phi, eta = TestFunctions(VVQ)
u,p = TrialFunctions(VVQ)
w = Function(V2)

u0 = Function(V1)
u1 = Function(V1)
w0 = Function(V2)
U1 = Function(V2)

dt = 0.01
k = Constant(dt)
#EkPa = '62500'
#E = Constant(float(EkPa))

rho_f = 1000.0
nu = 0.001
mu_f = rho_f*nu
#nu = mu_f/rho_f
lamda = Constant("0.0105e9")
mu_s = Constant("1.0e12")
rho_s =Constant("1.0e6")


def sigma_structure(d):
    return 2*mu_s*sym(grad(d)) + lamda*tr(sym(grad(d)))*Identity(2)

def sigma_fluid(p,u):
    return -p*Identity(2) + mu_f * (nabla_grad(u) + nabla_grad(u).T)#sym(grad(u))


# Fluid variational form
F = rho_f*((1./k)*inner(u-u1,phi)*dx \
    + inner(dot(u1, grad(u)), phi) * dx) \
    + inner(sigma_fluid(p,u),grad(phi))*dx - inner(div(u),eta)*dx

# Structure Variational form
#U = U1 + w*k

#G = rho_s*((1./k)*inner(w-w0,psi))*dx(2) + inner(sigma_structure(U),grad(psi))*dx(2)

# Mesh movement, solving the equation laplace -nabla(grad(d))

#H = inner(grad(U),grad(psi))*dx(1) - inner(grad(U("-"))*n("-"),psi("-"))*dS(4)

#print assemble(n*Constant((0,1))*dS(4))

a = lhs(F)# - lhs(G) - lhs(H)
L = rhs(F)# - rhs(G) - rhs(H)

#F1 = F-G-H

def integrateFluidStress(u, p):

    eps   = 0.5*(nabla_grad(u) + nabla_grad(u).T)
    sig   = -p*Identity(len(u)) + 2.0*mu_f*eps

    traction  = dot(sig, n)

    forceX  = traction[0]*ds(1)
    forceY  = traction[1]*ds(1)
    fX      = assemble(forceX)
    fY      = assemble(forceY)

    return fX, fY

T = 1.0
t = 0.0
up = Function(VVQ)

u_file = File("results/velocity/velocity.pvd")
u_file << u0

Drag = []
Lift = []
del_p = []
time = []
x0 = np.where(mesh.coordinates()[:,0]==0.6)
x1 = np.where(mesh.coordinates()[:,0]==0.15)

#A = assemble(a)

while t < T:
    #if MPI.rank(mpi_comm_world()) == 0:
    eps = 10
    k_iter = 0
    max_iter = 10
    #while eps > 1E-6 and k_iter < max_iter:
    #b = assemble(L)

    #A.ident_zeros()
    #[bc.apply(A,b) for bc in bcs]
    #solve(A,up.vector(),b)
    solve(a==L,up,bcs)
    u_,p_ = up.split(True)

    drag,lift =integrateFluidStress(u_, p_)
    print "Time: ",t ," drag: ",drag, "lift: ",lift

    #print "Inlet velocity ", assemble(dot(u_,n)*ds(2))
    #print norm(u_), norm(u1)
    #eps = errornorm(u_,u0,degree_rise=3)
    #k_iter += 1
    #print "k: ",k_iter, "error: %.3e" %eps
    #u0.assign(u_)
    #w0.assign(w_)
    #w_.vector()[:] *= float(k)
    #U1.vector = w_.vector()[:]
    #ALE.move(mesh,w_)
    #mesh.bounding_box_tree().build(mesh)
    u1.assign(u_)

    #plot(u_)
    #CALCULATE LIFT AND Drag
    R = VectorFunctionSpace(mesh, 'R', 0)
    c = TestFunction(R)
    tau = -p_*Identity(2)+mu_f*(grad(u1)+grad(u_).T)
    forces = -assemble(dot(dot(tau, n), c)*ds(1)).array()
    Drag.append(forces[0]); Lift.append(forces[1])
    #p1 = p_.compute_vertex_values()
    #diff_p = p1[x0[0]]-p1[x1[0]]
    #del_p.append(diff_p)
    #time.append(t)
    print "At time t=", t, "   Drag", forces[0], "lift", forces[1]

    u_file << u_
    #print "Time:",t

    t += dt
Drag[0] = 0; Lift[0] = 0
print "max Drag",max(Drag), "max Lift",max(Lift)

np.savetxt('results/drag.txt', Drag, delimiter=',')
np.savetxt('results/left.txt', Lift, delimiter=',')
np.savetxt('results/pressure.txt', del_p, delimiter=',')
np.savetxt('results/time.txt', time, delimiter=',')
plot(u_,interactive=True)
