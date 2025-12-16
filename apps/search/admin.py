from django.contrib import admin
from .models import SearchKeyword, SearchHistory, ViewHistory


@admin.register(SearchKeyword)
class SearchKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'count')
    search_fields = ('keyword',)
    ordering = ('-count',)


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'query', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'query')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'listing', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'listing__title')
    readonly_fields = ('viewed_at',)
    date_hierarchy = 'viewed_at'
    raw_id_fields = ('user', 'listing')      # быстрый выбор при большом количестве записей

