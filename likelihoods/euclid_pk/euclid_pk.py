from likelihood_class import likelihood
import os
import numpy as np
from math import exp,log,sqrt,pi

class euclid_pk(likelihood):

  def __init__(self,path,data,command_line,log_flag,default):

    likelihood.__init__(self,path,data,command_line,log_flag,default)

    self.need_Class_arguments(data,{'output':'mPk'})
    
    #################
    # find number of galaxies for each mean redshift value
    #################

    # Compute the number of galaxies for each \bar z
    # For this, one needs dn/dz TODO
    # then n_g(\bar z) = int_{\bar z - dz/2}^{\bar z + dz/2} dn/dz dz
    # self.z_mean will contain the central values

    self.n_g = np.zeros(self.nbin,'float64')
    self.z_mean = np.zeros(self.nbin,'float64')
    i=0
    for z in np.arange(self.zmin,self.zmax+self.dz,self.dz):
      self.z_mean[i] = z
      i+=1

    # Store the z edge values
    self.z_edges = np.zeros(self.nbin+1,'float64')
    i = 0
    for z in np.arange(self.zmin-self.dz/2.,self.zmax+self.dz,self.dz):
      self.z_edges[i] = z
      i+=1

    # Store the total vector z, with edges + mean
    self.z = np.zeros(2*self.nbin+1,'float64')
    i=0
    for z in np.arange(self.zmin-self.dz/2.,self.zmax+self.dz,self.dz/2.):
      self.z[i] = z
      i+=1

    # For each bin, compute the biais function,
    self.b = np.zeros(self.nbin,'float64')
    for Bin in range(self.nbin):
      self.b[Bin] = sqrt(self.z_mean[Bin]+1.)

    self.need_Class_arguments(data,{'z_max_pk':self.z[-1]})

    # Force Class to store Pk for k up to an arbitrary number (since self.r is not yet decided)... TODO
    self.need_Class_arguments(data,{'P_k_max_1/Mpc':1.5*self.kmax})

    # In case of a comparison, stop here
    if not default:
      return

    # Define the k values for the integration (from kmin to kmax), at which the
    # spectrum will be computed (and stored for the fiducial model)
    # k_size is deeply arbitrary here, TODO
    
    self.k_size = 100
    self.k_fid = np.zeros(self.k_size,'float64')
    for i in range(self.k_size):
      self.k_fid[i] = exp( i*1.0 /(self.k_size-1) * log(self.kmax/self.kmin) + log(self.kmin))

    ################
    # Noise spectrum TODO properly
    ################

    self.n_g = np.zeros(self.nbin,'float64')
    #for index_z in range(self.nbin):
      #print self.z_mean[index_z],self.z[2*index_z],self.z[2*index_z+2]
      #self.n_g[index_z] = self.galaxy_distribution(self.z[2*index_z+2]) - self.galaxy_distribution(self.z[2*index_z])
    #print self.n_g

    self.n_g[0] = 6844.945
    self.n_g[1] = 7129.45
    self.n_g[2] = 7249.912
    self.n_g[3] = 7261.722
    self.n_g[4] = 7203.825
    self.n_g[5] = 7103.047
    self.n_g[6] = 6977.571
    self.n_g[7] = 6839.546
    self.n_g[8] = 6696.957
    self.n_g[9] = 5496.988
    self.n_g[10] = 4459.240
    self.n_g[11] = 3577.143
    self.n_g[12] = 2838.767
    self.n_g[13] = 2229.282
    self.n_g[14] = 1732.706
    self.n_g[15] = 1333.091

    # If the file exists, initialize the fiducial values,
    # the spectrum will be read first, with k_size values of k and nbin values
    # of z. Then, H_fid and D_A fid will be read (each with nbin values).
    #self.Cl_fid = np.zeros((self.nlmax,self.nbin,self.nbin),'float64')
    self.fid_values_exist = False
    self.pk_nl_fid = np.zeros((self.k_size,2*self.nbin+1),'float64')
    self.H_fid       = np.zeros(2*self.nbin+1,'float64')
    self.D_A_fid     = np.zeros(2*self.nbin+1,'float64') 
    self.sigma_r_fid = np.zeros(self.nbin,'float64')

    if os.path.exists(self.data_directory+'/'+self.fiducial_file):
      self.fid_values_exist = True
      fid_file = open(self.data_directory+'/'+self.fiducial_file,'r')
      line = fid_file.readline()
      while line.find('#')!=-1:
	line = fid_file.readline()
      while (line.find('\n')!=-1 and len(line)==1):
	line = fid_file.readline()
      for index_k in range(self.k_size):
	for index_z in range(2*self.nbin+1):
	  self.pk_nl_fid[index_k,index_z] = float(line)
	  line = fid_file.readline()
      for index_z in range(2*self.nbin+1):
	self.H_fid[index_z]   = float(line.split()[0])
	self.D_A_fid[index_z] = float(line.split()[1])
	line = fid_file.readline()
      for index_z in range(self.nbin):
	self.sigma_r_fid[index_z] = float(line)
	line = fid_file.readline()
      fid_file.seek(0)
      fid_file.close()
      
    # Else the file will be created in the loglkl() function. 
    return
  
  # Galaxy distribution, returns the function D(z) from the notes
  def galaxy_distribution(self,z):

    zmean = 0.9
    z0 = zmean/1.412

    galaxy_dist = z**2*exp(-(z/z0)**(1.5))
    
    return galaxy_dist

  def loglkl(self,_cosmo,data):
    # First thing, recover the angular distance and Hubble factor for each
    # redshift
    H   = np.zeros(2*self.nbin+1,'float64')
    D_A = np.zeros(2*self.nbin+1,'float64') 
    r   = np.zeros(2*self.nbin+1,'float64')

    # H is incidentally also dz/dr
    r,H = _cosmo.z_of_r(self.z)
    D_A = _cosmo._angular_distance(self.z)
    #for Bin in range(self.nbin+2):
      #print '%.4g %.4g %.4g %.4g' % (H[Bin],D_A[Bin],self.H_fid[Bin],self.D_A_fid[Bin])
    #exit()

    # Compute sigma_r = dr(z)/dz sigma_z with sigma_z = 0.001(1+z)
    sigma_r = np.zeros(self.nbin,'float64')
    for index_z in range(self.nbin):
      sigma_r[index_z] = 0.001*(1.+self.z_mean[index_z])/H[2*index_z+1]

    # Compute V_survey, for each given redshift bin, which is the volume of a
    # shell times the sky coverage:
    self.V_survey = np.zeros(self.nbin,'float64')
    for index_z in range(self.nbin):
      self.V_survey[index_z] = 4.*pi*(r[2*index_z+1]**2)*(1+self.z_mean[index_z])**-3 *self.dz/H[2*index_z+1]
    
    # Define the mu scale
    mu = np.zeros(self.mu_size,'float64')
    for index_mu in range(self.mu_size):
      mu[index_mu] = 2.*(index_mu)/(self.mu_size-1) - 1.

    # If the fiducial model does not exists, recover the power spectrum and
    # store it, then exit.
    if self.fid_values_exist is False:
      pk = np.zeros((self.k_size,2*self.nbin+1),'float64')
      fid_file = open(self.data_directory+'/'+self.fiducial_file,'w')
      fid_file.write('# Fiducial parameters')
      for key,value in data.mcmc_parameters.iteritems():
	fid_file.write(', %s = %.5g' % (key,value['current']*value['initial'][4]))
      fid_file.write('\n')
      for index_k in range(self.k_size):
	for index_z in range(2*self.nbin+1):
	  pk[index_k,index_z] = _cosmo._pk(self.k_fid[index_k],self.z[index_z])
	  fid_file.write('%.8g\n' % pk[index_k,index_z])
      for index_z in range(2*self.nbin+1):
	fid_file.write('%.8g %.8g\n' % (H[index_z],D_A[index_z]))
      for index_z in range(self.nbin):
	fid_file.write('%.8g\n' % sigma_r[index_z])
      print '\n\n /|\  Writting fiducial model in {0}, exiting now'.format(self.data_directory+self.fiducial_file)
      print '/_o_\ You should restart a new chain'
      exit()

    # Compute the beta_fid function, for observed spectrum,
    # beta_fid(k_fid,z) = 1/2b(z) * d log(P_nl_fid(k_fid,z))/d log a
    #                   = -1/2b(z)* (1+z) d log(P_nl_fid(k_fid,z))/dz 
    beta_fid = np.zeros((self.k_size,self.nbin),'float64')
    for index_k in range(self.k_size):
      for index_z in range(self.nbin):
	beta_fid[index_k,index_z] = -1./(2.*self.b[index_z]) * (1.+self.z_mean[index_z]) * log(self.pk_nl_fid[index_k,2*index_z+2] / self.pk_nl_fid[index_k,2*index_z])/(2.*self.dz)

    # Compute the tilde P_fid(k_ref,z,mu) = H_fid(z)/D_A_fid(z)**2 ( 1 + beta_fid(k_fid,z)mu^2)^2 P_nl_fid(k_fid,z)exp ( -k_fid^2 mu^2 sigma_r_fid^2)
    self.tilde_P_fid = np.zeros((self.k_size,self.nbin,self.mu_size),'float64')
    for index_k in range(self.k_size):
      for index_z in range(self.nbin):
	for index_mu in range(self.mu_size):
	  self.tilde_P_fid[index_k,index_z,index_mu] = self.H_fid[2*index_z+1]/(self.D_A_fid[2*index_z+1]**2) * (1. + beta_fid[index_k,index_z]*(mu[index_mu]**2))**2 * self.pk_nl_fid[index_k,2*index_z+1]*exp( - self.k_fid[index_k]**2 *mu[index_mu]**2*self.sigma_r_fid[index_z]**2)

    ######################
    # TH PART
    ###################### 
    # Compute values of k based on k_fid (ref in paper), with formula (33 has to be corrected):
    # k^2 = ( (1-mu^2) D_A_fid(z)^2/D_A(z)^2 + mu^2 H(z)^2/H_fid(z)^2) k_fid ^ 2
    # So k = k (k_ref,z,mu)
    self.k = np.zeros((self.k_size,2*self.nbin+1,self.mu_size),'float64')
    for index_k in range(self.k_size):
      for index_z in range(2*self.nbin+1):
	for index_mu in range(self.mu_size):
	  self.k[index_k,index_z,index_mu] = sqrt((1.-mu[index_mu]**2)*self.D_A_fid[index_z]**2/D_A[index_z]**2 + mu[index_mu]**2*H[index_z]**2/self.H_fid[index_z]**2 )*self.k_fid[index_k]

    # Recover the non-linear power spectrum from the cosmological module on all
    # the z_boundaries, to compute afterwards beta. This is pk_nl_th from the
    # notes.
    pk_nl_th = np.zeros((self.k_size,2*self.nbin+1,self.mu_size),'float64')
    for index_k in range(self.k_size):
      for index_z in range(2*self.nbin+1):
	for index_mu in range(self.mu_size):
	  pk_nl_th[index_k,index_z,index_mu] = _cosmo._pk(self.k[index_k,index_z,index_mu],self.z[index_z])

    # Compute the beta function for nl, 
    # beta(k,z) = 1/2b(z) * d log(P_nl_th (k,z))/d log a
    #   	= -1/2b(z) *(1+z) d log(P_nl_th (k,z))/dz 
    beta_th = np.zeros((self.k_size,self.nbin,self.mu_size),'float64')
    for index_k in range(self.k_size):
      for index_z in range(self.nbin):
	for index_mu in range(self.mu_size):
	  beta_th[index_k,index_z,index_mu] = -1./(2.*self.b[index_z]) * (1.+self.z_mean[index_z]) * log(pk_nl_th[index_k,2*index_z+2,index_mu]/pk_nl_th[index_k,2*index_z,index_mu])/(2.*self.dz)
    
    # Compute \tilde P_th(k,mu,z) = H(z)/D_A(z)^2 * (1 + beta(z,k) mu^2)^2 P_nl_th (k,z) exp(-k^2 mu^2 sigma_r^2)
    self.tilde_P_th = np.zeros( (self.k_size,self.nbin,self.mu_size), 'float64')
    for index_k in range(self.k_size):
      for index_z in range(self.nbin):
	for index_mu in range(self.mu_size):
	  self.tilde_P_th[index_k,index_z,index_mu] = H[2*index_z+1]/(D_A[2*index_z+1]**2) * (1. + beta_th[index_k,index_z,index_mu]*mu[index_mu]*mu[index_mu])**2* pk_nl_th[index_k,2*index_z+1,index_mu]*exp(-self.k[index_k,2*index_z+1,index_mu]**2*mu[index_mu]**2*sigma_r[index_z]**2)

    # Shot noise spectrum, deduced from the nuisance parameter P_shot
    self.P_shot = np.zeros( (self.nbin),'float64')
    for index_z in range(self.nbin):
      self.P_shot[index_z] = self.H_fid[2*index_z+1]/(self.D_A_fid[2*index_z+1]**2*self.b[index_z]**2)*(data.mcmc_parameters['P_shot']['current']*data.mcmc_parameters['P_shot']['initial'][4] + 1./self.n_g[index_z])
      
    # finally compute chi2, for each z_mean
    chi2 = 0.0
    mu_integrand_lo,mu_integrand_hi = 0.0,0.0
    k_integrand_lo,k_integrand_hi   = 0.0,0.0
    for index_z in range(self.nbin):
      # integrate over mu
      # compute first the value in mu = lower bound = -1
      k_integrand_hi = self.integrand(0,index_z,0)
      for index_k in range(1,self.k_size):
	k_integrand_lo = k_integrand_hi
	k_integrand_hi = self.integrand(index_k,index_z,0)
	mu_integrand_hi += (k_integrand_hi + k_integrand_lo)/2.*(self.k_fid[index_k] - self.k_fid[index_k-1])
      for index_mu in range(1,self.mu_size):
	mu_integrand_lo = mu_integrand_hi
	mu_integrand_hi = 0
	k_integrand_hi = self.integrand(0,index_z,index_mu)
	for index_k in range(1,self.k_size):
	  k_integrand_lo = k_integrand_hi
	  k_integrand_hi = self.integrand(index_k,index_z,index_mu)
	  mu_integrand_hi += (k_integrand_hi + k_integrand_lo)/2.*(self.k_fid[index_k] - self.k_fid[index_k-1])
	chi2 += (mu_integrand_hi + mu_integrand_lo)/2.*(mu[index_mu] - mu[index_mu-1])

    return - chi2/2.

  def integrand(self,index_k,index_z,index_mu):
    return self.k_fid[index_k]**2/(2.*pi)**2*self.V_survey[index_z]/2.*((self.tilde_P_th[index_k,index_z,index_mu] - self.tilde_P_fid[index_k,index_z,index_mu])/(self.tilde_P_th[index_k,index_z,index_mu]+self.P_shot[index_z]))**2
