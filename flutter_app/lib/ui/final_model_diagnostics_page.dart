import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../services/final_model_runtime_diagnostics.dart';
import '../services/label_service.dart';
import '../services/tflite_sign_classifier.dart';
import '../theme/signsync_theme.dart';
import 'widgets/section_header.dart';

typedef FinalModelDiagnosticsLoader =
    Future<FinalModelDiagnosticsData> Function();

class FinalModelDiagnosticsData {
  const FinalModelDiagnosticsData({
    required this.metadata,
    required this.modelLoaded,
    required this.contractValidated,
    this.error,
  });

  final LabelMetadata metadata;
  final bool modelLoaded;
  final bool contractValidated;
  final String? error;

  bool get passed =>
      modelLoaded &&
      contractValidated &&
      metadata.queryMappingMatches &&
      error == null;
}

class FinalModelDiagnosticsPage extends StatefulWidget {
  const FinalModelDiagnosticsPage({super.key, this.loader});

  final FinalModelDiagnosticsLoader? loader;

  @override
  State<FinalModelDiagnosticsPage> createState() =>
      _FinalModelDiagnosticsPageState();
}

class _FinalModelDiagnosticsPageState extends State<FinalModelDiagnosticsPage> {
  FinalModelDiagnosticsData? _data;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await (widget.loader ?? _loadProductionDiagnostics)();
      if (!mounted) {
        return;
      }
      setState(() => _data = data);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _loadError = error.toString());
    }
  }

  Future<FinalModelDiagnosticsData> _loadProductionDiagnostics() async {
    final metadata = await LabelService().load();
    final classifier = TfliteSignClassifier(metadata: metadata);
    try {
      await classifier.load();
      return FinalModelDiagnosticsData(
        metadata: metadata,
        modelLoaded: classifier.isLoaded,
        contractValidated: classifier.contractValidated,
        error: classifier.diagnosticError,
      );
    } finally {
      classifier.close();
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return Scaffold(
      appBar: AppBar(title: const Text('Final Model Diagnostics')),
      body: SafeArea(
        child: data == null && _loadError == null
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
                children: [
                  _ContractStatus(
                    passed: data?.passed == true,
                    error: _loadError ?? data?.error,
                  ),
                  if (data != null) ...[
                    const SizedBox(height: 24),
                    const SectionHeader(
                      title: 'Active model',
                      description:
                          'Read-only local deployment information for project verification.',
                    ),
                    const SizedBox(height: 8),
                    _InfoRow(
                      label: 'Model version',
                      value: AppConfig.modelVersion,
                    ),
                    _InfoRow(
                      label: 'Deployment status',
                      value: AppConfig.deploymentStatus,
                    ),
                    const _InfoRow(
                      label: 'Default model',
                      value: 'Dynamic-range TFLite',
                    ),
                    const _InfoRow(label: 'Input shape', value: '[1, 756]'),
                    const _InfoRow(label: 'Output shape', value: '[1, 40]'),
                    const _InfoRow(
                      label: 'Labels',
                      value: '40 banking intents',
                    ),
                    const _InfoRow(label: 'Feature count', value: '756'),
                    _InfoRow(
                      label: 'Confidence threshold',
                      value: AppConfig.bankingIntentConfidenceThreshold
                          .toStringAsFixed(2),
                    ),
                    _InfoRow(
                      label: 'Query mapping',
                      value: data.metadata.queryMappingMatches
                          ? 'PASS - exact 40-label order'
                          : 'FAIL',
                    ),
                    _InfoRow(
                      label: 'TFLite load',
                      value: data.modelLoaded ? 'PASS' : 'FAIL',
                    ),
                    _InfoRow(
                      label: 'Tensor contract',
                      value: data.contractValidated ? 'PASS' : 'FAIL',
                    ),
                    const _InfoRow(
                      label: 'Android package',
                      value: AppConfig.androidPackageId,
                    ),
                    const SizedBox(height: 24),
                    const SectionHeader(title: 'Model artifacts'),
                    const SizedBox(height: 8),
                    ..._artifactRows(data.metadata.deploymentManifest),
                    const SizedBox(height: 24),
                    const SectionHeader(
                      title: 'Latest in-memory timing',
                      description:
                          'Cleared when the process ends; no interaction history is stored.',
                    ),
                    const SizedBox(height: 8),
                    _InfoRow(
                      label: 'Model load',
                      value: _milliseconds(
                        FinalModelRuntimeDiagnostics.modelLoadMs,
                      ),
                    ),
                    _InfoRow(
                      label: 'Feature computation',
                      value: _milliseconds(
                        FinalModelRuntimeDiagnostics.featureComputationMs,
                      ),
                    ),
                    _InfoRow(
                      label: 'TFLite inference',
                      value: _milliseconds(
                        FinalModelRuntimeDiagnostics.inferenceMs,
                      ),
                    ),
                    _InfoRow(
                      label: 'Prediction processing',
                      value: _milliseconds(
                        FinalModelRuntimeDiagnostics.predictionProcessingMs,
                      ),
                    ),
                  ],
                ],
              ),
      ),
    );
  }

  List<Widget> _artifactRows(Map<String, Object?> manifest) {
    final hashes = manifest['deployed_asset_sha256'] as Map<String, Object?>;
    final sizes = manifest['model_file_sizes_bytes'] as Map<String, Object?>;
    return <Widget>[
      _InfoRow(
        label: 'Dynamic model size',
        value: '${sizes['dynamic_range']} bytes',
      ),
      _InfoRow(label: 'Float32 model size', value: '${sizes['float32']} bytes'),
      _HashRow(
        label: 'Dynamic SHA-256',
        hash: hashes['dynamic_range'].toString(),
      ),
      _HashRow(label: 'Float32 SHA-256', hash: hashes['float32'].toString()),
      _HashRow(label: 'Labels SHA-256', hash: hashes['labels'].toString()),
    ];
  }

  String _milliseconds(double? value) {
    return value == null
        ? 'Not measured in this session'
        : '${value.toStringAsFixed(3)} ms';
  }
}

class _ContractStatus extends StatelessWidget {
  const _ContractStatus({required this.passed, required this.error});

  final bool passed;
  final String? error;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      key: const ValueKey('final-model-contract-status'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: passed ? colors.primaryContainer : colors.errorContainer,
        borderRadius: BorderRadius.circular(SignSyncTheme.radius),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            passed ? Icons.verified_outlined : Icons.error_outline,
            color: passed ? colors.onPrimaryContainer : colors.onErrorContainer,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  passed
                      ? 'Contract validation PASS'
                      : 'Contract validation FAIL',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                if (error != null) ...[
                  const SizedBox(height: 4),
                  SelectableText(error!),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 142,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _HashRow extends StatelessWidget {
  const _HashRow({required this.label, required this.hash});

  final String label;
  final String hash;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Expanded(
            child: _InfoRow(
              label: label,
              value:
                  '${hash.substring(0, 12)}...${hash.substring(hash.length - 8)}',
            ),
          ),
          IconButton(
            tooltip: 'Copy full SHA-256',
            onPressed: () => Clipboard.setData(ClipboardData(text: hash)),
            icon: const Icon(Icons.copy_outlined),
          ),
        ],
      ),
    );
  }
}
