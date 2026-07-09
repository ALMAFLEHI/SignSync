import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../config/app_config.dart';
import '../models/live_landmark_frame.dart';
import '../models/live_prediction_session.dart';
import '../services/live_landmark_service.dart';
import '../services/phone_sample_store.dart';

class PhoneDatasetCollectionPage extends StatefulWidget {
  const PhoneDatasetCollectionPage({super.key});

  @override
  State<PhoneDatasetCollectionPage> createState() =>
      _PhoneDatasetCollectionPageState();
}

class _PhoneDatasetCollectionPageState
    extends State<PhoneDatasetCollectionPage> {
  late final LiveLandmarkService _landmarkService;

  PhoneSampleStore? _sampleStore;
  LiveLandmarkFrame? _lastFrame;
  String _selectedLabel = PhoneSampleStore.weakLabels.first;
  String _statusMessage = 'Preparing phone dataset collection...';
  String? _errorMessage;
  String? _sampleDirectoryPath;
  PhoneSampleSaveResult? _lastSaveResult;
  Map<String, int> _counts = {
    for (final label in PhoneSampleStore.weakLabels) label: 0,
  };
  bool _isCameraStarting = false;
  bool _isCameraStarted = false;
  bool _isCapturing = false;
  bool _isSaving = false;
  int _validFrameCount = 0;

  @override
  void initState() {
    super.initState();
    _landmarkService = LiveLandmarkService()
      ..onStatus = _handleStatus
      ..onError = _handleError
      ..onFrame = _handleLiveFrame
      ..onCaptureProgress = _handleCaptureProgress
      ..onCaptureComplete = _handleCaptureComplete;
    _initializeStorage();
  }

  @override
  void dispose() {
    unawaited(_landmarkService.dispose());
    super.dispose();
  }

  Future<void> _initializeStorage() async {
    if (!Platform.isAndroid) {
      setState(() {
        _statusMessage = 'Phone sample collection is available on Android.';
        _errorMessage = 'Run this page on the Samsung Android phone.';
      });
      return;
    }

    try {
      final directoryPath = await _landmarkService.getPhoneSampleDirectory();
      final store = PhoneSampleStore(directoryPath: directoryPath);
      final counts = await store.countSamplesByLabel();
      if (!mounted) {
        return;
      }
      setState(() {
        _sampleStore = store;
        _sampleDirectoryPath = directoryPath;
        _counts = counts;
        _statusMessage = 'Ready to collect phone-camera landmark samples.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.toString();
        _statusMessage = 'Could not prepare phone sample storage.';
      });
    }
  }

  Future<void> _startCamera() async {
    if (!Platform.isAndroid) {
      setState(() {
        _errorMessage = 'Phone dataset collection requires Android.';
      });
      return;
    }

    setState(() {
      _isCameraStarting = true;
      _errorMessage = null;
      _statusMessage = 'Requesting camera permission...';
    });

    final permission = await Permission.camera.request();
    if (!mounted) {
      return;
    }
    if (!permission.isGranted) {
      setState(() {
        _isCameraStarting = false;
        _errorMessage = 'Camera permission was denied.';
        _statusMessage = 'Grant camera permission before collecting samples.';
      });
      return;
    }

    try {
      await _landmarkService.startCamera();
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarted = true;
        _isCameraStarting = false;
        _statusMessage = 'Camera started. Select a weak label and capture.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarting = false;
        _errorMessage = error.toString();
        _statusMessage = 'Camera could not start.';
      });
    }
  }

  Future<void> _startCapture() async {
    if (_sampleStore == null) {
      setState(() {
        _errorMessage = 'Phone sample storage is not ready yet.';
      });
      return;
    }
    if (!_isCameraStarted) {
      setState(() {
        _errorMessage = 'Start the camera before capturing a sample.';
      });
      return;
    }

    setState(() {
      _validFrameCount = 0;
      _lastSaveResult = null;
      _isCapturing = true;
      _isSaving = false;
      _errorMessage = null;
      _statusMessage =
          'Capturing ${AppConfig.expectedFrameCount} valid landmark frames for $_selectedLabel...';
    });
    await _landmarkService.startCapture();
  }

  Future<void> _resetCapture() async {
    await _landmarkService.resetCapture();
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = 0;
      _isCapturing = false;
      _isSaving = false;
      _lastSaveResult = null;
      _statusMessage = 'Capture reset.';
    });
  }

  void _handleStatus(String message) {
    if (!mounted || message.isEmpty) {
      return;
    }
    setState(() {
      _statusMessage = message;
    });
  }

  void _handleError(String message) {
    if (!mounted) {
      return;
    }
    setState(() {
      _errorMessage = message.isEmpty ? 'Phone sample capture error.' : message;
      _isCameraStarting = false;
    });
  }

  void _handleLiveFrame(LiveLandmarkFrame frame) {
    if (!mounted) {
      return;
    }
    setState(() {
      _lastFrame = frame;
    });
  }

  void _handleCaptureProgress(int validFrameCount, int requiredFrameCount) {
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = validFrameCount;
      _isCapturing = validFrameCount < requiredFrameCount;
    });
  }

  Future<void> _handleCaptureComplete(
    List<List<double>> frames,
    LiveCaptureMetrics _,
  ) async {
    final store = _sampleStore;
    if (store == null) {
      return;
    }

    setState(() {
      _isCapturing = false;
      _isSaving = true;
      _statusMessage = 'Saving phone sample JSON...';
    });

    try {
      final result = await store.saveSample(
        label: _selectedLabel,
        frames: frames,
      );
      final counts = await store.countSamplesByLabel();
      if (!mounted) {
        return;
      }
      setState(() {
        _isSaving = false;
        _lastSaveResult = result;
        _counts = counts;
        _validFrameCount = AppConfig.expectedFrameCount;
        _statusMessage = 'Saved ${result.sampleId}.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isSaving = false;
        _errorMessage = error.toString();
        _statusMessage = 'Could not save phone sample.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final lastFrame = _lastFrame;

    return Scaffold(
      appBar: AppBar(title: const Text('Phone Dataset Collection')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _Header(statusMessage: _statusMessage),
            if (_errorMessage != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _errorMessage!),
            ],
            const SizedBox(height: 12),
            _CameraPreviewCard(preview: _landmarkService.buildPreview()),
            const SizedBox(height: 12),
            _LabelSelector(
              selectedLabel: _selectedLabel,
              counts: _counts,
              onChanged: _isCapturing || _isSaving
                  ? null
                  : (label) {
                      setState(() {
                        _selectedLabel = label;
                        _lastSaveResult = null;
                      });
                    },
            ),
            const SizedBox(height: 12),
            _CollectionStatusCard(
              cameraStarted: _isCameraStarted,
              lastFrame: lastFrame,
              validFrameCount: _validFrameCount,
              isCapturing: _isCapturing,
              directoryPath: _sampleDirectoryPath,
            ),
            const SizedBox(height: 12),
            _ControlPanel(
              isCameraStarting: _isCameraStarting,
              isCameraStarted: _isCameraStarted,
              isCapturing: _isCapturing,
              isSaving: _isSaving,
              onStartCamera: _startCamera,
              onStartCapture: _startCapture,
              onResetCapture: _resetCapture,
            ),
            if (_lastSaveResult != null) ...[
              const SizedBox(height: 12),
              _SaveResultCard(result: _lastSaveResult!),
            ],
            const SizedBox(height: 12),
            const _PrivacyCard(),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.statusMessage});

  final String statusMessage;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sprint 2.16A Phone Dataset Pilot',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 4),
        Text(
          statusMessage,
          style: const TextStyle(
            color: Color(0xFF0F766E),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _CameraPreviewCard extends StatelessWidget {
  const _CameraPreviewCard({required this.preview});

  final Widget preview;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: AspectRatio(aspectRatio: 3 / 4, child: preview),
    );
  }
}

class _LabelSelector extends StatelessWidget {
  const _LabelSelector({
    required this.selectedLabel,
    required this.counts,
    required this.onChanged,
  });

  final String selectedLabel;
  final Map<String, int> counts;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Weak Label Target',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            for (final label in PhoneSampleStore.weakLabels) ...[
              _LabelOption(
                label: label,
                count: counts[label] ?? 0,
                selected: selectedLabel == label,
                onTap: onChanged == null ? null : () => onChanged!(label),
              ),
              if (label != PhoneSampleStore.weakLabels.last)
                const SizedBox(height: 8),
            ],
          ],
        ),
      ),
    );
  }
}

class _LabelOption extends StatelessWidget {
  const _LabelOption({
    required this.label,
    required this.count,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final int count;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final remaining = (PhoneSampleStore.targetSamplesPerLabel - count).clamp(
      0,
      PhoneSampleStore.targetSamplesPerLabel,
    );
    return Material(
      color: selected
          ? colorScheme.primary.withValues(alpha: 0.08)
          : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: selected ? colorScheme.primary : const Color(0xFFE2E8F0),
          width: selected ? 1.5 : 1,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              Icon(
                selected
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
                color: selected ? colorScheme.primary : const Color(0xFF94A3B8),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: selected ? colorScheme.primary : null,
                  ),
                ),
              ),
              Text('$count / ${PhoneSampleStore.targetSamplesPerLabel}'),
              const SizedBox(width: 8),
              Text(
                remaining == 0 ? 'done' : '$remaining left',
                style: const TextStyle(color: Color(0xFF64748B)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CollectionStatusCard extends StatelessWidget {
  const _CollectionStatusCard({
    required this.cameraStarted,
    required this.lastFrame,
    required this.validFrameCount,
    required this.isCapturing,
    required this.directoryPath,
  });

  final bool cameraStarted;
  final LiveLandmarkFrame? lastFrame;
  final int validFrameCount;
  final bool isCapturing;
  final String? directoryPath;

  @override
  Widget build(BuildContext context) {
    final frame = lastFrame;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Sample Capture Status',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'Camera preview',
              value: cameraStarted ? 'Started' : 'Stopped',
            ),
            _StatusRow(
              label: 'Hand detected',
              value: frame?.handDetected == true ? 'Yes' : 'No',
            ),
            _StatusRow(
              label: 'Frame dimension',
              value: frame?.isValid == true
                  ? AppConfig.expectedFrameWidth.toString()
                  : 'Waiting',
            ),
            _StatusRow(
              label: 'Valid frame buffer',
              value: '$validFrameCount / ${AppConfig.expectedFrameCount}',
            ),
            if (directoryPath != null)
              _StatusRow(label: 'Save folder', value: directoryPath!),
            if (isCapturing) const SizedBox(height: 8),
            if (isCapturing)
              LinearProgressIndicator(
                value: validFrameCount / AppConfig.expectedFrameCount,
              ),
          ],
        ),
      ),
    );
  }
}

class _ControlPanel extends StatelessWidget {
  const _ControlPanel({
    required this.isCameraStarting,
    required this.isCameraStarted,
    required this.isCapturing,
    required this.isSaving,
    required this.onStartCamera,
    required this.onStartCapture,
    required this.onResetCapture,
  });

  final bool isCameraStarting;
  final bool isCameraStarted;
  final bool isCapturing;
  final bool isSaving;
  final VoidCallback onStartCamera;
  final VoidCallback onStartCapture;
  final VoidCallback onResetCapture;

  @override
  Widget build(BuildContext context) {
    final disabled = isCameraStarting || isCapturing || isSaving;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton.icon(
              onPressed: disabled || isCameraStarted ? null : onStartCamera,
              icon: isCameraStarting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.videocam),
              label: const Text('Start Camera'),
            ),
            FilledButton.icon(
              onPressed: disabled || !isCameraStarted ? null : onStartCapture,
              icon: isSaving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save),
              label: const Text('Capture & Save Sample'),
            ),
            OutlinedButton.icon(
              onPressed: disabled ? null : onResetCapture,
              icon: const Icon(Icons.restart_alt),
              label: const Text('Reset'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SaveResultCard extends StatelessWidget {
  const _SaveResultCard({required this.result});

  final PhoneSampleSaveResult result;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Saved Sample',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(label: 'Sample ID', value: result.sampleId),
            _StatusRow(label: 'Label', value: result.label),
            _StatusRow(
              label: 'Repetition',
              value: 'R${result.repetition.toString().padLeft(2, '0')}',
            ),
            _StatusRow(label: 'Path', value: result.path),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
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

class _PrivacyCard extends StatelessWidget {
  const _PrivacyCard();

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
                'Only landmark JSON samples are saved locally. No raw video is saved or uploaded.',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
