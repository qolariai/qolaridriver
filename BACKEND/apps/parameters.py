# -*- coding: utf-8 -*-
"""Parametros moveis (experiencias/flags) que as apps pedem por gRPC ao arrancar e depois do login.

Driver: `ow2.g0.g` -> ParametersServingClient -> ParameterServingPresentationGrpcApi
(`api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/...`).
O arranque da Driver (`s75.b`) so passa do splash quando a obtencao autenticada acaba em SUCCESS.
Resposta vazia = sucesso com 0 parametros: a app fica com os valores por omissao gravados na APK.
"""
from apps.grpc import grpc_handles

SVC = "/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation"


@grpc_handles(("driver",), SVC + "/GetMobileParameters", SVC + "/GetMobileParametersUnauthenticated",
              SVC + "/GetMobilePrioritizedParameters")
def mobile_parameters(app, fields, raw):
    return b""
