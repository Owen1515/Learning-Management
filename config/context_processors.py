def school_profile(request):
    try:
        from academics.models import SchoolProfile
        profile = SchoolProfile.objects.first()
    except Exception:
        profile = None
    return {"school_profile": profile}
