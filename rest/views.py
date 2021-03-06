# -*- coding: utf-8 -*-
from django.http import Http404
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import NotAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, \
    UpdateModelMixin

from sendfile import sendfile
import logging

from judge.models import Submission, Problem, PrintRequest

from .models import Node
from .serializers import SubmissionSerializer, TestsTimestampsSerializer,\
    PrintRequestSerializer


LOGGER = logging.getLogger(__name__)


class SubmissionViewSet(ListModelMixin, RetrieveModelMixin,
                        UpdateModelMixin, GenericViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    @list_route()
    def for_judging(self, request, *args, **kwargs):
        """Get a submission for judging."""
        token = request.META.get('HTTP_X_TOKEN')

        try:
            node = Node.objects.get(token=token)
        except ObjectDoesNotExist:
            raise NotAuthenticated(detail="Unrecognized node token")

        try:
            with transaction.atomic():
                queryset = self.get_queryset().select_for_update()
                instance = queryset.filter(
                    status=Submission.WAITING_STATUS
                ).earliest('timestamp')
                instance.status = Submission.JUDGING_STATUS
                instance.node = node
                instance.results.all().delete()
                instance.save()
        except ObjectDoesNotExist:
            raise Http404

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProblemViewSet(GenericViewSet):

    queryset = Problem.objects.all()
    lookup_field = 'codename'

    @detail_route()
    def test_input(self, request, *args, **kwargs):
        problem = self.get_object()
        return sendfile(request, problem.tests.input.file.path)

    @detail_route()
    def test_output(self, request, *args, **kwargs):
        problem = self.get_object()
        return sendfile(request, problem.tests.output.file.path)

    @detail_route()
    def test_config(self, request, *args, **kwargs):
        problem = self.get_object()
        return sendfile(request, problem.tests.config.file.path)

    @detail_route()
    def test_timestamps(self, *args, **kwargs):
        problem = self.get_object()
        serializer = TestsTimestampsSerializer(problem.tests)
        return Response(serializer.data)


class PrintRequestViewSet(ListModelMixin, RetrieveModelMixin,
                          UpdateModelMixin, GenericViewSet):
    queryset = PrintRequest.objects.all()
    serializer_class = PrintRequestSerializer

    @list_route()
    def for_printing(self, request, *args, **kwargs):
        """Get a printRequest for printing."""

        try:
            with transaction.atomic():
                queryset = self.get_queryset().select_for_update()
                instance = queryset.filter(
                    status=PrintRequest.WAITING_STATUS
                ).earliest('timestamp')
                instance.status = PrintRequest.PRINTING_STATUS
                instance.save()
        except ObjectDoesNotExist:
            raise Http404

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


router = DefaultRouter()
router.register(r'printrequest', PrintRequestViewSet)
router.register(r'submission', SubmissionViewSet)
router.register(r'problem', ProblemViewSet)
