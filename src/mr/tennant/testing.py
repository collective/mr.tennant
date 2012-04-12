from plone.testing import Layer
from plone.testing import z2

class David_Testing(Layer):
    defaultBases = (z2.STARTUP, )


DAVID_FIXTURE = David_Testing()

DAVID_INTEGRATION_TESTING = z2.IntegrationTesting(bases=(DAVID_FIXTURE,), name="DavidFixture:Integration")
