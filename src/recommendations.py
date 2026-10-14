from backend.app.services.recommendation_service import recommendation_service

def get_recommendations():
    """Wrapper calling backend recommendations service."""
    return recommendation_service.generate_recommendations()
