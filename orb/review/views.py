from functools import wraps
from datetime import date, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required

from orb.decorators import reviewer_required
from orb.models import Resource, ResourceCriteria, ReviewerRole
from .forms import ReviewForm, RejectionForm, AssignmentForm, AssignmentFormSet, StaffReviewForm
from .models import ContentReview


def resource_review(func):
    """View decorator that gets the matching review"""
    @wraps(func)
    def decorator(request, resource_id, review_id):
        review = get_object_or_404(
            ContentReview.objects.select_related(),
            pk=review_id,
            resource__pk=resource_id,
        )
        if request.user != review.reviewer:
            raise PermissionDenied
        return func(request, review)
    return decorator


@reviewer_required
@resource_review
def review_resource(request, review):
    """
    Renders/processes the form for adding a resource review.

    Args:
        request: the HttpRequest
        review: the selected review instance

    Returns:
        HttpResponse

    """
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data['approved']
            if approved:
                review.approve()
                review.save()
                messages.success(request, _(u"Thank you for reviewing this content"))
            else:
                review.reject()
                review.save()
                messages.success(request, _(u"Thank you for reviewing this content"))
            return redirect("orb_pending_resources")
    else:
        form = ReviewForm()

    return render(request, "orb/review/review_form.html", {
        'review': review,
        'form': form,
        'criteria': ResourceCriteria.objects.all(),
    })


@reviewer_required
@resource_review
def reject_resource(request, review):
    """
    View that handles

    Args:
        request: the HttpRequest
        review: the selected review instance

    Returns:
        HttpResponse

    """
    if not review.is_pending:
        messages.info(request, _(u"You cannot review this content again."))
        return redirect("orb_pending_resources")

    if request.method == 'POST':
        form = RejectionForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.reject()
            review.save()
            messages.success(request, _(u"Thank you for reviewing this content"))
            return redirect("orb_pending_resources")
    else:
        form = RejectionForm()
    return render(request, "orb/review/reject_form.html", {
        'form': form,
        'resource': review.resource,
    })


@reviewer_required
def resource_review_list(request):
    """
    View that lists resources that are pending review
    """

    role_queries = [
        Q(content_reviews__status=Resource.PENDING) & Q(content_reviews__role=role)
        for role in ReviewerRole.roles.all()
    ]
    query = Q()
    for role_query in role_queries:
        query = query | role_query

    overdue_resources = Resource.resources.pending().filter(
        content_reviews__status=Resource.PENDING,
        content_reviews__update_date__lte=date.today() - timedelta(days=7),
    )

    unassigned_resources = Resource.resources.pending().exclude(*(query,))
    pending_resources = Resource.resources.pending()
    review_assignments = ContentReview.reviews.pending().for_user(request.user)

    overdue_reviews = ContentReview.reviews.overdue()

    return render(request, "orb/review/review_list.html",{
        'pending_resources': pending_resources,
        'unassigned_resources': unassigned_resources,
        'review_assignments': review_assignments,
        'overdue_resources': overdue_resources,
        'overdue_reviews': overdue_reviews,
    })


@reviewer_required
def assign_review(request, resource_id):

    resource = get_object_or_404(Resource, pk=resource_id)
    if request.method == 'POST':
        form = AssignmentForm(resource=resource, data=request.POST)
        if form.is_valid():
            form.save()

    else:
        form = AssignmentForm(resource=resource)

    return render(request, "orb/review/assign_review.html",{
        'resource': resource,
        'form': form,
    })


@staff_member_required
def delete_resource(request, resource_id):
    """

    Args:
        request: HttpRequest object
        resource_id: the primary key of the Resource

    Returns:

    """
    resource = get_object_or_404(Resource, pk=resource_id)
    if request.method in ['POST', 'DELETE']:
        if not resource.is_pending():
            messages.error(request, _(u"You cannot delete non-pending resources"))
            return redirect("orb_pending_resources")
        if resource.has_assignments():
            messages.error(
                request, _(u"You cannot delete resources with existing review assignemnts"))
            return redirect("orb_pending_resources")
        resource.delete()
        messages.success(request, _(u"The resource was deleted"))
        return redirect("orb_pending_resources")
    return render(request, "orb/resource/confirm_delete.html", {'resource': resource})


@staff_member_required
def staff_review(request, resource_id):
    """
    Allows a staff user to quickly approve/reject a resource, short
    circuiting the complete review process.

    Args:
        request: HttpRequest object
        resource_id: the primary key of the Resource

    Returns:
        HttpResponse

    """
    resource = get_object_or_404(Resource, pk=resource_id)
    if request.method == 'POST':
        form = StaffReviewForm(resource=resource, data=request.POST)
        if form.is_valid():
            message_level, message = form.save()
            messages.add_message(request, message_level, message)
            return redirect("orb_pending_resources")
    else:
        form = StaffReviewForm(resource=resource)
    return render(request, "orb/review/staff_review.html", {
        'resource': resource,
        'form': form,
        'criteria': ResourceCriteria.objects.all(),
    })
