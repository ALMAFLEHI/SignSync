import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';
import '../services/label_service.dart';
import '../services/test_feature_loader.dart';
import '../services/tflite_sign_classifier.dart';
import 'widgets/mode_selector.dart';
import 'widgets/prediction_card.dart';
import 'widgets/test_sample_buttons.dart';
import 'widgets/top_predictions_list.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final LabelService _labelService = LabelService();
  final TestFeatureLoader _testFeatureLoader = TestFeatureLoader();

  LabelMetadata? _metadata;
  TfliteSignClassifier? _classifier;
  SignMode _selectedMode = SignMode.normal;
  TestFeatureSample? _selectedSample;
  PredictionResult? _prediction;
  String? _statusMessage;
  String? _errorMessage;
  bool _isLoading = true;
  bool _isPredicting = false;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  @override
  void dispose() {
    _classifier?.close();
    super.dispose();
  }

  Future<void> _initialize() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = 'Loading labels and TFLite model...';
    });

    try {
      final metadata = await _labelService.load();
      setState(() {
        _metadata = metadata;
        _statusMessage = 'Label metadata loaded. Loading TFLite model...';
      });

      final classifier = TfliteSignClassifier(metadata: metadata);
      await classifier.load();

      setState(() {
        _classifier = classifier;
        _statusMessage = 'Ready for offline test feature inference.';
        _isLoading = false;
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
        _statusMessage = _metadata == null
            ? 'Setup failed. Check model assets and metadata.'
            : 'Label metadata loaded. TFLite runtime is not available yet.';
        _isLoading = false;
      });
    }
  }

  Future<void> _runSample(String sampleId) async {
    final classifier = _classifier;
    if (classifier == null || !classifier.isLoaded) {
      setState(() {
        _errorMessage = 'Model is not loaded yet.';
      });
      return;
    }

    setState(() {
      _isPredicting = true;
      _errorMessage = null;
    });

    try {
      final sample = await _testFeatureLoader.load(sampleId);
      final prediction = classifier.predict(sample.features, _selectedMode);
      setState(() {
        _selectedSample = sample;
        _prediction = prediction;
        _isPredicting = false;
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
        _isPredicting = false;
      });
    }
  }

  void _updateMode(SignMode mode) {
    setState(() {
      _selectedMode = mode;
      _prediction = null;
      _selectedSample = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final classifier = _classifier;

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appTitle),
        actions: [
          IconButton(
            tooltip: 'Reload assets',
            onPressed: _isLoading ? null : _initialize,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _Header(statusMessage: _statusMessage),
            const SizedBox(height: 12),
            _StatusPanel(
              labelsLoaded: _metadata != null,
              modelLoaded: classifier?.isLoaded ?? false,
              selectedModel:
                  classifier?.selectedModelAsset ??
                  AppConfig.dynamicRangeModelAsset,
              isLoading: _isLoading,
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _errorMessage!),
            ],
            const SizedBox(height: 12),
            ModeSelector(selectedMode: _selectedMode, onChanged: _updateMode),
            const SizedBox(height: 12),
            TestSampleButtons(
              enabled: !_isLoading && !_isPredicting && classifier != null,
              onSampleSelected: _runSample,
            ),
            const SizedBox(height: 12),
            PredictionCard(
              sample: _selectedSample,
              prediction: _prediction,
              isPredicting: _isPredicting,
            ),
            if (_prediction != null) ...[
              const SizedBox(height: 12),
              TopPredictionsList(
                title: '${_selectedMode.displayName} Top Predictions',
                predictions: _prediction!.topPredictions,
              ),
              const SizedBox(height: 12),
              TopPredictionsList(
                title: 'Raw Model Top Predictions',
                predictions: _prediction!.rawTopPredictions,
              ),
            ],
            const SizedBox(height: 12),
            const _PrivacyPanel(),
            const SizedBox(height: 12),
            const _NextSprintPanel(),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.statusMessage});

  final String? statusMessage;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppConfig.appTitle,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.w700,
            color: const Color(0xFF102A43),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          AppConfig.appSubtitle,
          style: Theme.of(
            context,
          ).textTheme.bodyLarge?.copyWith(color: const Color(0xFF486581)),
        ),
        const SizedBox(height: 8),
        Text(
          statusMessage ?? '',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: const Color(0xFF0F766E),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _StatusPanel extends StatelessWidget {
  const _StatusPanel({
    required this.labelsLoaded,
    required this.modelLoaded,
    required this.selectedModel,
    required this.isLoading,
  });

  final bool labelsLoaded;
  final bool modelLoaded;
  final String selectedModel;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Prototype Status',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              icon: labelsLoaded ? Icons.check_circle : Icons.pending,
              label: 'Label metadata',
              value: labelsLoaded ? 'Loaded' : 'Not loaded',
            ),
            _StatusRow(
              icon: modelLoaded ? Icons.check_circle : Icons.pending,
              label: 'TFLite model',
              value: isLoading
                  ? 'Loading'
                  : (modelLoaded ? 'Loaded' : 'Not loaded'),
            ),
            _StatusRow(
              icon: Icons.memory,
              label: 'Selected model',
              value: selectedModel.split('/').last,
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text(label)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFFFF1F2),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFBE123C)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Color(0xFF9F1239)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrivacyPanel extends StatelessWidget {
  const _PrivacyPanel();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.lock_outline, color: Color(0xFF0F766E)),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Offline on-device inference. No video upload is used in this prototype.',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NextSprintPanel extends StatelessWidget {
  const _NextSprintPanel();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.videocam_outlined, color: Color(0xFF64748B)),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Live camera landmark capture will be added in Sprint 2.15.',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
