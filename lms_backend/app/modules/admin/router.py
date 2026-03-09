from fastapi import APIRouter

from .approvals.router import router as approvals_router
from .audit.router import router as audit_router
from .emi.router import router as emi_router
from .staff.router import router as staff_router
from .support.router import router as support_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(approvals_router)
router.include_router(audit_router)
router.include_router(emi_router)
router.include_router(staff_router)
router.include_router(support_router)
