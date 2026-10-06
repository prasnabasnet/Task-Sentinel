from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import RelatedDropdownFilter

from apps.comments.models import Comment


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = (
        "display_comment_snippet",
        "author",
        "display_target_object",
        "display_mentions_count",
        "created_at",
    )
    list_display_links = ("display_comment_snippet",)

    search_fields = (
        "body",
        "author__email",
        "author__username",
    )
    list_filter = (
        ("author", RelatedDropdownFilter),
        "content_type",
        "created_at",
    )
    autocomplete_fields = ("author", "parent", "mentions")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Comment Body",
            {
                "fields": ("body", "parent"),
            },
        ),
        (
            "Author & Mentions",
            {
                "fields": ("author", "mentions"),
            },
        ),
        (
            "Generic Target Relation",
            {
                "fields": ("content_type", "object_id"),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @display(description="Comment", header=True)
    def display_comment_snippet(self, obj):
        snippet = obj.body[:60] + "..." if len(obj.body) > 60 else obj.body
        return [
            snippet,
            f"By {obj.author.username if obj.author else 'Unknown'}",
            None,
        ]

    @display(description="Attached To", label="info")
    def display_target_object(self, obj):
        if obj.commentable_object:
            return str(obj.commentable_object)
        return f"{obj.content_type} (ID: {obj.object_id})"

    @display(description="Mentions", label="primary")
    def display_mentions_count(self, obj):
        return f"{obj.mentions.count()} User(s)"
