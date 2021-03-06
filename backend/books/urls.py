from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.get_index_info),
    path('detail/<id>', views.detail),
    path('list/<type_id>/<sort>/<yorn>', views.list),
    path('', views.BooksListViewSet.as_view({'get': 'list'})),
    path('dump', views.dumpData),
]
