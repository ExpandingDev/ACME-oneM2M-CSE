#
#	testEnableShortResourceExpiration.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name enableShortResourceExpiration
@usage (Tests) Enable shorter resource expirations: enableShortResourceExpiration <seconds>
@uppertester

if ${argc} != 1
	error Wrong number of arguments: enableShortResourceExpiration <expirationInterval>
	quit
endif

##################################################################

# Store and then set the CSE's expiration check expirationInterval
storagePut cse.checkExpirationsInterval ${cse.checkExpirationsInterval}
setConfig cse.checkExpirationsInterval ${argv 1}

# Store and then set the CSE's minimum ET value for <request> resources
storagePut cse.req.minet ${cse.req.minet}
setConfig cse.req.minet ${argv 1}

# Return the cse.maxExpirationDelta
quit ${storageGet cse.checkExpirationsInterval},${cse.maxExpirationDelta}
