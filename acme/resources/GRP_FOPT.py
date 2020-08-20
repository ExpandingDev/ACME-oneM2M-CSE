#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: fanOutPoint (virtual resource)
#

from flask import Request
from Constants import Constants as C
import CSE
from .Resource import *
from Logging import Logging
from Types import ResourceTypes as T, Result


# TODO:
# - Handle Group Request Target Members parameter
# - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

class GRP_FOPT(Resource):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.GRP_FOPT, jsn, pi, create=create, inheritACP=True, readOnly=True, rn='fopt', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def handleRetrieveRequest(self, request:Request, id:str, originator:str) -> Result:
		Logging.logDebug('Retrieving resources from fopt')
		return CSE.group.foptRequest(C.opRETRIEVE, self, request, id, originator)


	def handleCreateRequest(self, request: Request, id:str, originator:str, ct:str, ty:T) -> Result:
		Logging.logDebug('Creating resources at fopt')
		return CSE.group.foptRequest(C.opCREATE, self, request, id, originator, ct, ty)


	def handleUpdateRequest(self, request: Request, id: str, originator: str, ct: str) -> Result:
		Logging.logDebug('Updating resources at fopt')
		return CSE.group.foptRequest(C.opUPDATE, self, request, id, originator, ct)


	def handleDeleteRequest(self, request: Request, id: str, originator: str) -> Result:
		Logging.logDebug('Deleting resources at fopt')
		return CSE.group.foptRequest(C.opDELETE, self, request, id, originator)


