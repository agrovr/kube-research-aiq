{{- define "kube-research-aiq.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "kube-research-aiq.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "kube-research-aiq.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "kube-research-aiq.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "kube-research-aiq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "kube-research-aiq.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kube-research-aiq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "kube-research-aiq.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "kube-research-aiq.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "kube-research-aiq.redisUrl" -}}
redis://{{ include "kube-research-aiq.fullname" . }}-redis:6379/0
{{- end -}}

{{- define "kube-research-aiq.postgresDsn" -}}
postgresql://{{ .Values.postgres.username }}:{{ .Values.postgres.password }}@{{ include "kube-research-aiq.fullname" . }}-postgres:5432/{{ .Values.postgres.database }}
{{- end -}}
