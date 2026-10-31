from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import ContactInquiryForm


@ensure_csrf_cookie
def school_contact(request):
    if request.method == "GET":
        return render(request, "school_site/contact.html")
    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    form = ContactInquiryForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    if not form.cleaned_data["website"]:
        form.save()
    return JsonResponse({
        "success": True,
        "message": "Thank you. Your enquiry has been sent to the school for follow-up.",
    })
