from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class AnonBurstRateThrottle(AnonRateThrottle):
    rate = '60/minute'

class AnonSustainedRateThrottle(AnonRateThrottle):
    rate = '1000/day'

class UserBurstRateThrottle(UserRateThrottle):
    rate = '120/minute'

class UserSustainedRateThrottle(UserRateThrottle):
    rate = '5000/day' 