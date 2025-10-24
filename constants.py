from enum import IntEnum

from unit_tool import Units
#u = Units(system='MKS')
u = Units()

class EtabsError(Exception):
    """Error general de ETABS."""
    pass

class eUnits(IntEnum):
    lb_in_F = 1
    lb_ft_F = 2
    kip_in_F = 3
    kip_ft_F = 4
    kN_mm_C = 5
    kN_m_C = 6
    kgf_mm_C = 7
    kgf_m_C = 8
    N_mm_C = 9
    N_m_C = 10
    Ton_mm_C = 11
    Ton_m_C = 12
    kN_cm_C = 13
    kgf_cm_C = 14
    N_cm_C = 15
    Ton_cm_C = 16

class eFramePropType(IntEnum):
    I = 1
    Channel = 2
    T = 3
    Angle = 4
    DblAngle = 5
    Box = 6
    Pipe = 7
    Rectangular = 8
    Circle = 9
    General = 10
    DbChannel = 11
    Auto = 12
    SD = 13
    Variable = 14
    Joist = 15
    Bridge = 16
    Cold_C = 17
    Cold_2C = 18
    Cold_Z = 19
    Cold_L = 20
    Cold_2L = 21
    Cold_Hat = 22
    BuiltupICoverplate = 23
    PCCGirderI = 24
    PCCGirderU = 25
    BuiltupIHybrid = 26
    BuiltupUHybrid = 27
    Concrete_L = 28
    FilledTube = 29
    FilledPipe = 30
    EncasedRectangle = 31
    EncasedCircle = 32
    BucklingRestrainedBrace = 33
    CoreBrace_BRB = 34
    ConcreteTee = 35
    ConcreteBox = 36
    ConcretePipe = 37
    ConcreteCross = 38
    SteelPlate = 39
    SteelRod = 40
    PCCGirderSuperT = 41
    Cold_Box = 42
    Cold_I = 43
    Cold_Pipe = 44
    Cold_T = 45
    Trapezoidal = 46
    PCCGirderBox = 47
    
class eMatType(IntEnum):
    Steel = 1
    Concrete = 2
    NoDesign = 3
    Aluminum = 4
    ColdFormed = 5
    Rebar = 6
    Tendon = 7
    Masonry = 8
