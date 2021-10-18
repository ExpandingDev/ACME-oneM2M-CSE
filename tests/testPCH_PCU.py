#
#	testPCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for PollingChannelURI functionality
#

import unittest, sys, time
from unittest.loader import findTestCases
import requests
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseStatusCode as RC, Permission
from init import *

aeRN2 = f'{aeRN}2'
ae2URL = f'{aeURL}2'
pch2URL = f'{ae2URL}/{pchRN}'
pcu2URL = f'{pch2URL}/pcu'

waitBetweenPollingRequests = sentRequestExpirationDelay/2.0 # seconds

class TestPCH_PCU(unittest.TestCase):

	ae 			= None
	cnt			= None
	ae2			= None
	acp2		= None
	originator 	= None
	originator2	= None
	aeRI		= None
	aeRI2		= None
	cntRI		= None
	acpRI2		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		"""	Setup the initial resource structure
		```
		CSEBase                             
		    ├─testAE                       
		    │    └─testCNT                 
		    └─testAE2                      
		         └─testACP2   Allows NOTIFY for testAE
		``` 
		"""


		# Add first AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : False,		# Explicitly not request reachable
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')

		# Add second AE that will receive notifications
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN2, 
					'api' : 'NMyAppId',
				 	'rr'  : False,		# Explicitly not request reachable
				 	'srv' : [ '3' ]
				}}
		cls.ae2, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator2 = findXPath(cls.ae2, 'm2m:ae/aei')
		cls.aeRI2 = findXPath(cls.ae2, 'm2m:ae/ri')

		# Add permissions for second AE
		dct = 	{ "m2m:acp": {
			"rn": f'{acpRN}2',
			"pv": {
				"acr": [ { 	
					"acor": [ cls.originator ],
					"acop": Permission.NOTIFY
				},
				{ 	
					"acor": [ cls.originator2 ],
					"acop": Permission.ALL
				} 
				]
			},
			"pvs": { 
				"acr": [ {
					"acor": [ cls.originator2 ],
					"acop": Permission.ALL
				} ]
			},
		}}
		cls.acp2, rsc = CREATE(ae2URL, cls.originator2, T.ACP, dct)
		assert rsc == RC.created, 'cannot create ACP'
		cls.acpRI2 = findXPath(cls.acp2, 'm2m:acp/ri')

		# Add acpi to second AE 
		dct = 	{ 'm2m:ae' : {
					'acpi' : [ cls.acpRI2 ]
				}}
		cls.ae, rsc = UPDATE(ae2URL, cls.originator2, dct)
		assert rsc == RC.updated, 'cannot update AE'
		
		# Add container to first AE
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(ae2URL, ORIGINATOR)	# Just delete the 2nd AE and everything below it. Ignore whether it exists or not

		with console.status('[bright_blue]Waiting for polling requests to timeout...') as status:
			time.sleep(sentRequestExpirationDelay)


	def _pollForRequest(self, originator:str, rcs:RC, isCreate:bool=False, isDelete:bool=False) -> None:
		r, rsc = RETRIEVE(pcu2URL, originator)	# polling request
		self.assertEqual(rsc, rcs, r)
		if rcs in [ RC.originatorHasNoPrivilege, RC.requestTimeout ]:
			return

		# response is a oneM2M request			
		self.assertIsNotNone(findXPath(r, 'm2m:rqp'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc/m2m:sgn'), r)
		if isCreate: self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc/m2m:sgn/vrq'), r)
		if isCreate: self.assertTrue(findXPath(r, 'm2m:rqp/pc/m2m:sgn/vrq'))
		if isDelete: self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc/m2m:sgn/sud'))
		if isDelete: self.assertTrue(findXPath(r, 'm2m:rqp/pc/m2m:sgn/sud'))
		self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc/m2m:sgn/sur'))
		if isCreate: self.assertIsNotNone(findXPath(r, 'm2m:rqp/pc/m2m:sgn/cr'))
		self.assertIsNotNone(findXPath(r, 'm2m:rqp/rqi'))
		rqi = findXPath(r, 'm2m:rqp/rqi')

		# Build and send OK response as a Notification
		dct = {
			'm2m:rsp' : {
				'fr'  : originator,	# TODO Configurable
				'rqi' : rqi,
				'rvi' : RVI,
				'rsc' : int(RC.OK)
			}
		}
		r, rsc = NOTIFY(pcu2URL, originator, data=dct)
	

	def _pollWhenCreating(self, originator:str, rcs:RC=RC.OK) -> Thread:
		# Start polling thread and wait moment before sending next request
		thread = Thread(target=self._pollForRequest, kwargs={'originator':originator, 'rcs':rcs, 'isCreate':True})
		thread.start()
		time.sleep(waitBetweenPollingRequests)	# Wait for delete notification
		return thread


	def _pollWhenDeleting(self,originator:str, rcs:RC=RC.OK) -> Thread:
		# Start polling thread and wait moment before sending next request
		thread = Thread(target=self._pollForRequest, kwargs={'originator':originator, 'rcs':rcs, 'isDelete':True})
		thread.start()
		time.sleep(waitBetweenPollingRequests)	# Wait for delete notification
		return thread


	def _waitForPolling(self, thread:Thread) -> None:
		thread.join()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBunderCNTFail(self) -> None:
		"""	CREATE <SUB> under <CNT>. No <PCH> yet -> FAIL"""
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.createDirectChild ]
					},
						'nu': [ TestPCH_PCU.aeRI2 ],
					# 'su': TestPCH_PCU.aeRI2
				}}
		r, rsc = CREATE(cntURL, TestPCH_PCU.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.subscriptionVerificationInitiationFailed, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCHunderAE2(self) -> None:
		"""	Create <PCH> under <AE> 2"""
		self.assertIsNotNone(TestPCH_PCU.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		r, rsc = CREATE(ae2URL, TestPCH_PCU.originator2, T.PCH, dct)
		self.assertEqual(rsc, RC.created, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCUunderAE2Fail(self) -> None:
		"""	Retrieve <PCU>'s with implicite request timeout (nothing to retrieve) -> FAIL """
		r, rsc = RETRIEVE(pcu2URL, TestPCH_PCU.originator2)
		self.assertEqual(rsc, RC.requestTimeout, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBunderCNT(self) -> None:
		"""	CREATE <SUB> under <CNT> with <PCH>"""

		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.createDirectChild ]
					},
					'nu': [ TestPCH_PCU.originator2 ],
					'su': TestPCH_PCU.originator2
				}}

		thread = self._pollWhenCreating(TestPCH_PCU.originator2)
		r, rsc = CREATE(cntURL, TestPCH_PCU.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created, r)
		self._waitForPolling(thread)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_DeleteSUBunderCNT(self) -> None:
		"""	DELETE <SUB> under <CNT> with <PCH>"""

		thread = self._pollWhenDeleting(TestPCH_PCU.originator2)
		r, rsc = DELETE(f'{cntURL}/{subRN}', TestPCH_PCU.originator)
		self.assertEqual(rsc, RC.deleted, r)
		self._waitForPolling(thread)
	


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUB2underCNTAnswerWithWrongTarget(self) -> None:
		"""	CREATE <SUB> under <CNT> with <PCH> (wrong target) -> Fail"""

		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.createDirectChild ]
					},
					'nu': [ TestPCH_PCU.originator ],
					'su': TestPCH_PCU.originator
				}}
		thread = self._pollWhenCreating(TestPCH_PCU.originator2, rcs=RC.requestTimeout)
		r, rsc = CREATE(cntURL, TestPCH_PCU.originator2, T.SUB, dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)
		self._waitForPolling(thread)
		# No <sub> created


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_accesPCUwithWrongOriginator(self) -> None:
		"""	RETRIEVE <PCU> with wrong originator -> Fail"""
		thread = self._pollWhenCreating(TestPCH_PCU.originator, rcs=RC.originatorHasNoPrivilege)
		thread.join()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_accessPCUwithshortExpiration(self) -> None:
		"""	RETRIEVE <PCU> with short expiration -> Fail"""
		r, rsc = RETRIEVE(pcu2URL, TestPCH_PCU.originator2, headers={C.hfRET : str(sentRequestExpirationDelay/2.0*1000)})	# polling request
		self.assertEqual(rsc, RC.requestTimeout, r)


	def test_createNotificationDoPolling(self) -> None:
		""" Create a <CIN> to create a notification and poll <PCU> """
		dct = 	{ 'm2m:cin' : {
					'con' : 'test'
				}}
		r, rsc = CREATE(cntURL, TestPCH_PCU.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, r)






# TODO: Add a CIN to create notification.


# TODO Non-Blocking async request, then retrieve notification via pcu
# TODO multiple non-blocking async requests, then retrieve notification via pcu

# TODO reply with notify but different originator -> Fail

# TODO return a wrong response 
# TODO return a empty response

# TODO retrieve via PCU *after* delete

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	enableShortSentRequestExpirations()
	if not isShortSentRequestExpirations():
		console.print('\n[red reverse] Error configuring the CSE\'s test settings ')
		console.print('Did you enable [i]remote configuration[/i] for the CSE?\n')
		return 0,0,1	

	# basic tests
	suite.addTest(TestPCH_PCU('test_createSUBunderCNTFail'))
	suite.addTest(TestPCH_PCU('test_createPCHunderAE2'))
	suite.addTest(TestPCH_PCU('test_accessPCUwithshortExpiration'))
	suite.addTest(TestPCH_PCU('test_retrievePCUunderAE2Fail'))
	suite.addTest(TestPCH_PCU('test_createSUBunderCNT'))
	suite.addTest(TestPCH_PCU('test_DeleteSUBunderCNT'))
	suite.addTest(TestPCH_PCU('test_accesPCUwithWrongOriginator'))
	suite.addTest(TestPCH_PCU('test_createSUB2underCNTAnswerWithWrongTarget'))

	# TODO suite.addTest(TestPCH_PCU('test_createNotificationDoPolling'))



	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	disableShortSentRequestExpirations()
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

