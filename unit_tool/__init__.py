from . import config

class Units:
    
    m : float
    cm : float
    mm : float
    inch : float
    N : float
    kN : float
    kg : float
    g : float
    kgf : float
    tonf : float
    Pa : float
    MPa : float
    s : float
    csi_units : str
    
    def __init__(self,system=None):
        self.system = None
        
        if system is None:
            system = config.units_system
        elif system not in ('SI','MKS','FPS'):
            return NotImplementedError(f'Sistema {system} no implementado')
        
        self.set_units(system)
        
    def get_system(self):
        return self.system
    
    def set_units(self,u_system='SI'):
        '''
        Establece los factores de conversion de acuerdo al sistema de unidades definido
        
        Parameters:
        u_system: str, default='SI'
            Sistema de unidades puede ser: 'SI'(Internacional),'MKS'(m-kg-s),'FPS'(ft-lb-s)
        '''
        if u_system != self.system:
            self.system = u_system
        else:
            return
        
        if u_system == 'SI':
            self.m = 1.
            self.kg = 1.
            self.s = 1
            self.csi_units = 'N_m_C'
        elif u_system == 'MKS':
            self.m = 1.
            self.kg = 1/9.8106
            self.s = 1.
            self.csi_units = 'kgf_m_C'
        elif u_system == 'FPS':
            self.m = 100/(2.54*12)
            self.kg = 1/2.20462
            self.s = 1.
            self.csi_units = 'lb_ft_F'
         
        self.lb = 2.20462*self.kg
        self.g = self.kg/1000
        self.cm = self.m/100
        self.mm = self.m/1000
        self.inch = 2.54*self.cm
        self.ft = self.inch*12
        self.N = self.kg*self.m/self.s**2
        self.kN = 1000*self.N
        self.kgf = self.N*9.8106
        self.tonf = 1000*self.kgf
        self.Pa = self.N/self.m**2
        self.MPa = 1e6*self.Pa
