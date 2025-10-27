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

class eLoadCaseType(IntEnum):
    LinearStatic = 1
    NonlinearStatic = 2
    Modal = 3
    ResponseSpectrum = 4
    LinearHistory = 5
    NonlinearHistory = 6
    LinearDynamic = 7
    NonlinearDynamic = 8
    MovingLoad = 9
    Buckling = 10
    SteadyState = 11
    PowerSpectralDensity = 12
    LinearStaticMultiStep = 13
    HyperStatic = 14

class eLoadPatternType(IntEnum):
    Dead = 1
    SuperDead = 2
    Live = 3
    ReduceLive = 4
    Quake = 5
    Wind = 6
    Snow = 7
    Other = 8
    Move = 9  # Not valid for ETABS and SAFE
    Temperature = 10
    Rooflive = 11
    Notional = 12
    PatternLive = 13
    Wave = 14  # Not valid for ETABS and SAFE
    Braking = 15  # Not valid for ETABS and SAFE
    Centrifugal = 16  # Not valid for ETABS and SAFE
    Friction = 17  # Not valid for ETABS and SAFE
    Ice = 18  # Not valid for ETABS and SAFE
    WindOnLiveLoad = 19  # Not valid for ETABS and SAFE
    HorizontalEarthPressure = 20  # Not valid for ETABS and SAFE
    VerticalEarthPressure = 21  # Not valid for ETABS and SAFE
    EarthSurcharge = 22  # Not valid for ETABS and SAFE
    DownDrag = 23  # Not valid for ETABS and SAFE
    VehicleCollision = 24  # Not valid for ETABS and SAFE
    VesselCollision = 25  # Not valid for ETABS and SAFE
    TemperatureGradient = 26  # Not valid for ETABS and SAFE
    Settlement = 27  # Not valid for ETABS and SAFE
    Shrinkage = 28  # Not valid for ETABS and SAFE
    Creep = 29  # Not valid for ETABS and SAFE
    WaterloadPressure = 30  # Not valid for ETABS and SAFE
    LiveLoadSurcharge = 31  # Not valid for ETABS and SAFE
    LockedInForces = 32  # Not valid for ETABS and SAFE
    PedestrianLL = 33  # Not valid for ETABS and SAFE
    Prestress = 34
    Hyperstatic = 35  # Not valid for ETABS and SAFE
    Bouyancy = 36  # Not valid for ETABS and SAFE
    StreamFlow = 37  # Not valid for ETABS and SAFE
    Impact = 38  # Not valid for ETABS and SAFE
    Construction = 39
    DeadWearing = 40  # Not valid for ETABS and SAFE
    DeadWater = 41  # Not valid for ETABS and SAFE
    DeadManufacture = 42  # Not valid for ETABS and SAFE
    EarthHydrostatic = 43  # Not valid for ETABS and SAFE
    PassiveEarthPressure = 44  # Not valid for ETABS and SAFE
    ActiveEarthPressure = 45  # Not valid for ETABS and SAFE
    PedestrianLLReduced = 46  # Not valid for ETABS and SAFE
    SnowHighAltitude = 47  # Not valid for ETABS and SAFE
    EuroLm1Char = 48  # Not valid for ETABS and SAFE
    EuroLm1Freq = 49  # Not valid for ETABS and SAFE
    EuroLm2 = 50  # Not valid for ETABS and SAFE
    EuroLm3 = 51  # Not valid for ETABS and SAFE
    EuroLm4 = 52  # Not valid for ETABS and SAFE
    SeaState = 53  # Not valid for ETABS and SAFE
    Permit = 54  # Not valid for ETABS and SAFE
    MoveFatigue = 55  # Not valid for ETABS and SAFE
    MoveFatiguePermit = 56  # Not valid for ETABS and SAFE
    MoveDeflection = 57  # Not valid for ETABS and SAFE
    MoveTrain = 58  # Not valid for ETABS and SAFE
    PrestressTransfer = 59
    PatternAuto = 60
    QuakeDrift = 61
    QuakeVerticalOnly = 62
