from django.contrib import admin
from .models import LibraryDocument, AIMarkingScheme


@admin.register(LibraryDocument)
class LibraryDocumentAdmin(admin.ModelAdmin):
    list_display  = ("title", "doc_type", "subject", "level", "uploaded_by", "is_visible", "created_at")
    list_filter   = ("doc_type", "subject", "level", "is_visible")
    search_fields = ("title", "description", "content")
    list_editable = ("is_visible",)
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Details", {
            "fields": ("title", "doc_type", "subject", "level", "description", "uploaded_by", "is_visible"),
        }),
        ("Content", {
            "description": "Provide either a file upload OR typed content (or both).",
            "fields": ("file", "content"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(AIMarkingScheme)
class AIMarkingSchemeAdmin(admin.ModelAdmin):
    list_display   = ("source_paper", "generated_by", "status", "created_at")
    list_filter    = ("status",)
    search_fields  = ("source_paper__title",)
    readonly_fields = ("created_at",)
