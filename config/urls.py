from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path(
        "media/<path:path>",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
    path(
        "admin/",
        admin.site.urls
    ),
    path(
        "fees/",
        include("fees.urls", namespace="fees")
    ),
    path(
        "library/",
        include("library.urls", namespace="library")
    ),
    path(
        "",
        TemplateView.as_view(template_name="school_site/home.html"),
        name="school_home"
    ),
    path(
        "about/",
        TemplateView.as_view(template_name="school_site/about.html"),
        name="school_about"
    ),
    path(
        "academics/",
        TemplateView.as_view(template_name="school_site/academics.html"),
        name="school_academics"
    ),
    path(
        "teachers/",
        TemplateView.as_view(template_name="school_site/teachers.html"),
        name="school_teachers"
    ),
    path(
        "gallery/",
        TemplateView.as_view(template_name="school_site/gallery.html"),
        name="school_gallery"
    ),
    path(
        "news/",
        TemplateView.as_view(template_name="school_site/news.html"),
        name="school_news"
    ),
    path(
        "events/",
        TemplateView.as_view(template_name="school_site/events.html"),
        name="school_events"
    ),
    path(
        "admissions/",
        TemplateView.as_view(template_name="school_site/admissions.html"),
        name="school_admissions"
    ),
    path(
        "contact/",
        TemplateView.as_view(template_name="school_site/contact.html"),
        name="school_contact"
    ),
    path(
        "ict/",
        TemplateView.as_view(template_name="school_site/ict.html"),
        name="school_ict"
    ),
    path(
        "development/",
        TemplateView.as_view(template_name="school_site/development.html"),
        name="school_development"
    ),
    path(
        "alumni/",
        TemplateView.as_view(template_name="school_site/alumni.html"),
        name="school_alumni"
    ),
    path(
        "documents/",
        TemplateView.as_view(template_name="school_site/documents.html"),
        name="school_documents"
    ),
    path(
        "",
        include("accounts.urls")
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
# Always serve media (WhiteNoise handles static; media served directly)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
