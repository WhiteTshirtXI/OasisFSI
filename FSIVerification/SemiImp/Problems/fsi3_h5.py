from dolfin import *
import numpy as np
import cPickle

mesh_file = Mesh("Mesh/fluid_new.xml")
#mesh_file = refine(mesh_file)
#Parameters for each numerical case
common = {"mesh": mesh_file,
          "v_deg": 2,    #Velocity degree
          "p_deg": 1,    #Pressure degree
          "d_deg": 2,    #Deformation degree
          "T": 20,          # End time
          "dt": 0.001,       # Time step
          "rho_f": 1.0E3,    #
          "mu_f": 1.,
          "rho_s" : Constant(1.0E3),
          "mu_s" : Constant(2.0E6),
          "nu_s" : Constant(0.4),
          "Um" : 2.0,
          "D" : 0.1,
          "H" : 0.41,
          "L" : 2.5,
          "step" : 20,
          "checkpoint": False
     }


vars().update(common)
lamda_s = nu_s*2*mu_s/(1 - 2.*nu_s)
#plot(mesh, interactive=True)

for coord in mesh.coordinates():
    if coord[0]==0.6 and (0.199<=coord[1]<=0.2001): # to get the point [0.2,0.6] end of bar
        print coord
        break
# BOUNDARIES

#NOS = AutoSubDomain(lambda x: "on_boundary" and( near(x[1],0) or near(x[1], 0.41)))
Inlet = AutoSubDomain(lambda x: "on_boundary" and near(x[0],0))
Outlet = AutoSubDomain(lambda x: "on_boundary" and (near(x[0],2.5)))
Wall =  AutoSubDomain(lambda x: "on_boundary" and (near(x[1], 0.41) or near(x[1], 0)))
Bar = AutoSubDomain(lambda x: "on_boundary" and (near(x[1], 0.21)) or near(x[1], 0.19) or near(x[0], 0.6 ) )
Circle =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  ))
Barwall =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  and x[1]>=0.19 and x[1]<=0.21 and x[0]>0.2 ))

Allboundaries = DomainBoundary()

boundaries = FacetFunction("size_t",mesh_file)
boundaries.set_all(0)
Allboundaries.mark(boundaries, 1)
Wall.mark(boundaries, 2)
Inlet.mark(boundaries, 3)
Outlet.mark(boundaries, 4)
Bar.mark(boundaries, 5)
Circle.mark(boundaries, 6)
Barwall.mark(boundaries, 7)
#plot(boundaries,interactive=True)

ds = Measure("ds", subdomain_data = boundaries)
dS = Measure("dS", subdomain_data = boundaries)
n = FacetNormal(mesh_file)

Bar_area = AutoSubDomain(lambda x: (0.19 <= x[1] <= 0.21) and 0.24<= x[0] <= 0.6) # only the "flag" or "bar"
domains = CellFunction("size_t", mesh_file)
domains.set_all(1)
Bar_area.mark(domains, 2) #Overwrites structure domain
dx = Measure("dx", subdomain_data = domains)
#plot(domains,interactive = True)
dx_f = dx(1, subdomain_data = domains)
dx_s = dx(2, subdomain_data = domains)
dis_x = []
dis_y = []
Drag_list = []
Lift_list = []
time_steps = []
#Fluid properties

class Inlet(Expression):
    def __init__(self, Um):
        self.t = 0
        self.U_in = Um
    def eval(self,value,x):
    	value[0] = 0.5*(1-np.cos(self.t*np.pi/2))*1.5*self.U_in*x[1]*(H-x[1])/((H/2.0)**2)
    	value[1] = 0
    def value_shape(self):
    	return (2,)

inlet = Inlet(Um)

def create_bcs(DVP, dvp_, n, k, Um, H, boundaries, Inlet, **semimp_namespace):
    #Fluid velocity conditions
    u_inlet  = DirichletBC(DVP.sub(1), inlet, boundaries, 3)
    u_wall   = DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 2)
    u_circ   = DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 6) #No slip on geometry in fluid
    u_barwall= DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 7) #No slip on geometry in fluid

    #displacement conditions:
    d_wall    = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 2)
    d_inlet   = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 3)
    d_outlet  = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 4)
    d_circle  = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 6)
    d_barwall = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 7) #No slip on geometry in fluid

    #Pressure Conditions
    p_out = DirichletBC(DVP.sub(2), 0, boundaries, 4)

    #Assemble boundary conditions
    bcs = [u_inlet, u_wall, u_circ, u_barwall,\
           d_wall, d_inlet, d_outlet, d_circle,d_barwall,\
           p_out]

    return dict(bcs = bcs, inlet = inlet)

def pre_solve(t, inlet, **semimp_namespace):
    if t < 2:
        inlet.t = t
    else:
        inlet.t = 2

    return dict(inlet = inlet)

def initiate(dt, v_deg, **monolithic):
    tic()
    #open("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/velocity.h5", "a").close()
    h5_u = HDF5File(mesh.mpi_comm(), "./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/velocity.h5", "w")
    h5_d = HDF5File(mesh.mpi_comm(), "./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/deformation.h5", "w")
    return dict(h5_u=h5_u, h5_d=h5_d)

def after_solve(t, dt, step, counter, time_steps, dvp_, h5_d, h5_u, n,coord,dis_x,dis_y,Drag_list,Lift_list, **semimp_namespace):

    d, v, p = dvp_["n"].split(True)

    if counter%step ==0:
        #h5_u << v
        #h5_d << d
        #h5_d.write(d)
        #h5_u.write(v)

        time_steps.append(t)
        h5_u.write(v, "/values_{}".format(len(time_steps)))
        h5_d.write(d, "/values_{}".format(len(time_steps)))

        #dvp_file << dvp_["n"]
        #dvp_file.write(dvp_["n"], "dvp%g"%t)


    def F_(U):
    	return (Identity(len(U)) + grad(U))

    def J_(U):
    	return det(F_(U))

    def sigma_f_new(v, p, d, mu_f):
    	return -p*Identity(len(v)) + mu_f*(grad(v)*inv(F_(d)) + inv(F_(d)).T*grad(v).T)

    #Fx = -assemble((sigma_f_new(v, p, d, mu_f)*n)[0]*ds(6))
    #Fy = -assemble((sigma_f_new(v, p, d, mu_f)*n)[1]*ds(6))
    #Fx += -assemble(((-p("-")*Identity(len(v)) + mu_f*(grad(v)("-")*inv(F_(d("-"))) + inv(F_(d("-"))).T*grad(v)("-").T))*n('-'))[0]*dS(5))
    #Fy += -assemble(((-p("-")*Identity(len(v)) + mu_f*(grad(v)("-")*inv(F_(d("-"))) + inv(F_(d("-"))).T*grad(v)("-").T))*n('-'))[1]*dS(5))
    Dr = -assemble((sigma_f_new(v,p,d,mu_f)*n)[0]*ds(6))
    Li = -assemble((sigma_f_new(v,p,d,mu_f)*n)[1]*ds(6))
    Dr += -assemble((sigma_f_new(v("-"),p("-"),d("-"),mu_f)*n("-"))[0]*dS(5))
    Li += -assemble((sigma_f_new(v("-"),p("-"),d("-"),mu_f)*n("-"))[1]*dS(5))
    Drag_list.append(Dr)
    Lift_list.append(Li)

    print "LIFT = %g,  DRAG = %g" % (Li, Dr)

    dsx = d(coord)[0]
    dsy = d(coord)[1]
    dis_x.append(dsx)
    dis_y.append(dsy)
    print "dis_x/dis_y : %g %g "%(dsx,dsy)

    return {}

def post_process(DVP, T,time_steps, h5_u, h5_d, v_deg, d_deg, dt,dis_x,dis_y, Drag_list,Lift_list, **semimp_namespace):
    #open("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/time_steps.cpickle", "w+").close()
    h5_u.close()
    h5_d.close()
    print "End time ", toc()
    """
    cPickle.dump(time_steps, open("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/times.cpickle", "w"))
    #if MPI.rank(mpi_comm_world()) == 0:
    time_steps  = cPickle.load(open("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/times.cpickle"))
    f_v = HDF5File(mesh.mpi_comm(),"./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/velocity.h5", "r")
    f_d = HDF5File(mesh.mpi_comm(),"./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/velocity.h5", "r")
    file_v = File("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/u.pvd")
    file_d = File("./FSI_fresh_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/d.pvd")

    d = Function(DVP.sub(0).collapse())
    v = Function(DVP.sub(1).collapse())
    for ind, t in enumerate(time_steps):
        f_v.read(v, "/values_{}".format(ind+1))
        f_d.read(d, "/values_{}".format(ind+1))
        file_v << (v,t)
        file_d << (d,t)
        #plot(u, title="u_{}".format(t))
        """
    """
    time_list = np.linspace(0,T,T/dt+1)
    plt.plot(time_list,dis_x); plt.ylabel("Displacement x");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/dis_x.png")
    plt.show()
    plt.plot(time_list,dis_y);plt.ylabel("Displacement y");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/dis_y.png")
    plt.show()
    plt.plot(time_list,Drag);plt.ylabel("Drag");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/drag.png")
    plt.show()
    plt.plot(time_list,Lift);plt.ylabel("Lift");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-3/P-"+str(v_deg) +"/dt-"+str(dt)+"/lift.png")
    plt.show()
    """
