import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from ..models.schemas import (
    NotificationListResponse,
    NotificationUnreadCountResponse,
    NotificationCheckResponse,
    NotificationMarkReadResponse,
    NotificationSeverity
)
from ..services.notification_service import notification_service

logger = logging.getLogger("energy_backend.routes.notifications")
router = APIRouter(prefix="/api/notifications", tags=["Notifications & Alerts"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    severity: Optional[str] = Query(None, description="Filter by severity: 'critical', 'warning', 'info'"),
    building: Optional[str] = Query(None, description="Filter by building / facility name"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    skip: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Retrieve energy notifications and alerts with optional filtering by read status, severity, and building.
    """
    try:
        if severity and severity.lower() not in [s.value for s in NotificationSeverity]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity '{severity}'. Valid values are: critical, warning, info"
            )
        return notification_service.list_notifications(
            unread_only=unread_only,
            severity=severity,
            building=building,
            limit=limit,
            skip=skip
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving notifications: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count():
    """
    Retrieve the current number of unread alerts for dashboard badges.
    """
    try:
        count = notification_service.get_unread_count()
        return NotificationUnreadCountResponse(unread_count=count)
    except Exception as e:
        logger.error("Error getting unread count: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch unread count: {str(e)}"
        )


@router.patch("/{notification_id}/read", response_model=NotificationMarkReadResponse)
def mark_notification_as_read(notification_id: str):
    """
    Mark an individual notification as read by ID.
    """
    try:
        return notification_service.mark_as_read(notification_id)
    except Exception as e:
        logger.error("Error marking notification %s as read: %s", notification_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
def mark_all_notifications_as_read():
    """
    Mark all unread notifications across the system as read.
    """
    try:
        return notification_service.mark_all_as_read()
    except Exception as e:
        logger.error("Error marking all notifications as read: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all as read: {str(e)}"
        )


@router.post("/check", response_model=NotificationCheckResponse)
def trigger_detection_check(
    peak_threshold_pct: float = Query(30.0, ge=10.0, le=90.0, description="Threshold percentage of total load for campus peak alerts"),
    surge_std_dev: float = Query(2.0, ge=1.0, le=5.0, description="Standard deviations above historical baseline to trigger surge alerts")
):
    """
    Trigger an alert detection scan across statistical anomalies, campus peak consumers,
    and facility-specific baseline surges. Deduplicates alerts to prevent redundant notifications.
    """
    try:
        return notification_service.run_detection_check(
            peak_threshold_pct=peak_threshold_pct,
            surge_std_dev=surge_std_dev
        )
    except Exception as e:
        logger.error("Error triggering detection check: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection check failed: {str(e)}"
        )


@router.delete("/{notification_id}")
def delete_notification(notification_id: str):
    """
    Delete a notification by ID.
    """
    try:
        deleted = notification_service.delete_notification(notification_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with id '{notification_id}' not found."
            )
        return {"success": True, "id": notification_id, "message": "Notification removed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notification %s: %s", notification_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )
