#
#	testDisableShortResourceExpiration.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name disableShortResourceExpiration
@usage (Tests) Disable shorter resource expirations: disableShortResourceExpiration
@uppertester

if ${argc} > 0
	error Wrong number of arguments: disableShortResourceExpiration
	quit
endif

##################################################################

# Restore the CSE's expiration check expirationInterval
if ${storageHas cse.checkExpirationsInterval}
	setConfig cse.checkExpirationsInterval ${storageGet cse.checkExpirationsInterval}
	storageRemove cse.checkExpirationsInterval
endif

# Restore the CSE's minimum ET value for <request> resources
if ${storageHas cse.req.minet}
	setConfig cse.req.minet ${storageGet cse.req.minet}
	storageRemove cse.req.minet
endif
