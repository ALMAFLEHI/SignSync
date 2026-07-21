import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../config/app_config.dart';
import '../config/phone_dataset_scope.dart';
import '../models/live_landmark_frame.dart';
import '../models/live_prediction_session.dart';
import '../services/live_landmark_service.dart';
import '../services/phone_sample_store.dart';

class PhoneDatasetCollectionPage extends StatefulWidget {
  const PhoneDatasetCollectionPage({super.key});

  static const Key cameraPreviewKey = ValueKey('phone-dataset-camera-preview');
  static const double cameraPreviewAspectRatio = 3 / 4;

  @override
  State<PhoneDatasetCollectionPage> createState() =>
      _PhoneDatasetCollectionPageState();
}

class _PhoneDatasetCollectionPageState
    extends State<PhoneDatasetCollectionPage> {
  late final LiveLandmarkService _landmarkService;

  PhoneSampleStore? _sampleStore;
  LiveLandmarkFrame? _lastFrame;
  String _selectedLabel = PhoneSampleStore.sprint216BCollectionLabels.first;
  String _statusMessage = 'Preparing phone dataset collection...';
  String? _errorMessage;
  String? _sampleDirectoryPath;
  PhoneSampleSaveResult? _lastSaveResult;
  Map<String, int> _counts = {
    for (final label in PhoneSampleStore.sprint216BCollectionLabels) label: 0,
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
        _statusMessage = 'Ready to collect the remaining 36 banking intents.';
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
        _statusMessage = 'Camera started. Select a banking label and capture.';
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
    if ((_counts[_selectedLabel] ?? 0) >= PhoneDatasetScope.samplesPerLabel) {
      setState(() {
        _errorMessage =
            '$_selectedLabel is complete at ${PhoneDatasetScope.samplesPerLabel}/'
            '${PhoneDatasetScope.samplesPerLabel}.';
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

  Future<void> _stopCamera() async {
    await _landmarkService.stopCamera();
    if (!mounted) {
      return;
    }
    setState(() {
      _isCameraStarted = false;
      _isCameraStarting = false;
      _isCapturing = false;
      _isSaving = false;
      _validFrameCount = 0;
      _lastFrame = null;
      _statusMessage = 'Camera stopped.';
    });
  }

  Future<void> _requestLabelChange(String label) async {
    if (label == _selectedLabel || _isCapturing || _isSaving) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Change collection label?'),
        content: Text(
          'Move from $_selectedLabel to $label? The next capture will be '
          'saved only under $label.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Change Label'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }
    setState(() {
      _selectedLabel = label;
      _lastSaveResult = null;
      _validFrameCount = 0;
      _errorMessage = null;
      _statusMessage = 'Selected $label.';
    });
  }

  Future<void> _selectNextIncomplete() async {
    final labels = PhoneSampleStore.sprint216BCollectionLabels;
    final startIndex = labels.indexOf(_selectedLabel);
    for (var offset = 1; offset <= labels.length; offset += 1) {
      final label = labels[(startIndex + offset) % labels.length];
      if ((_counts[label] ?? 0) < PhoneDatasetScope.samplesPerLabel) {
        await _requestLabelChange(label);
        return;
      }
    }
    setState(() {
      _statusMessage = 'All 36 Sprint 2.16B labels are complete.';
    });
  }

  Future<void> _deleteLastSavedSample() async {
    final store = _sampleStore;
    if (store == null || _isCapturing || _isSaving) {
      return;
    }
    try {
      final candidate = await store.lastSavedSampleForLabel(_selectedLabel);
      if (!mounted) {
        return;
      }
      if (candidate == null) {
        setState(() {
          _statusMessage = 'No valid saved sample exists for $_selectedLabel.';
        });
        return;
      }
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Delete last saved sample?'),
          content: Text(
            'Delete only ${candidate.sampleId} '
            '(R${PhoneSampleStore.formatRepetition(candidate.repetition)}) '
            'from $_selectedLabel?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Delete Sample'),
            ),
          ],
        ),
      );
      if (confirmed != true) {
        return;
      }
      final deleted = await store.deleteLastSavedSample(
        label: _selectedLabel,
        expectedSampleId: candidate.sampleId,
      );
      final counts = await store.countSamplesByLabel();
      if (!mounted) {
        return;
      }
      setState(() {
        _counts = counts;
        _lastSaveResult = null;
        _validFrameCount = 0;
        _statusMessage = 'Deleted ${deleted.sampleId} only.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.toString();
        _statusMessage = 'Could not delete the last saved sample.';
      });
    }
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
    final totalSamples = _counts.values.fold<int>(
      0,
      (total, count) => total + count,
    );
    final completedLabels = _counts.values
        .where((count) => count >= PhoneDatasetScope.samplesPerLabel)
        .length;
    final selectedComplete =
        (_counts[_selectedLabel] ?? 0) >= PhoneDatasetScope.samplesPerLabel;

    return Scaffold(
      appBar: AppBar(title: const Text('Sprint 2.16B Banking Collection')),
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
            _OverallProgressCard(
              selectedLabel: _selectedLabel,
              selectedCount: _counts[_selectedLabel] ?? 0,
              totalSamples: totalSamples,
              completedLabels: completedLabels,
            ),
            const SizedBox(height: 12),
            const _PilotSummaryCard(),
            const SizedBox(height: 12),
            _CameraPreviewCard(preview: _landmarkService.buildPreview()),
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
              selectedLabelComplete: selectedComplete,
              onStartCamera: _startCamera,
              onStartCapture: _startCapture,
              onResetCapture: _resetCapture,
              onStopCamera: _stopCamera,
              onDeleteLastSample: _deleteLastSavedSample,
            ),
            const SizedBox(height: 12),
            _LabelSelector(
              selectedLabel: _selectedLabel,
              counts: _counts,
              onChanged: _isCapturing || _isSaving ? null : _requestLabelChange,
              onSelectNext: _isCapturing || _isSaving
                  ? null
                  : _selectNextIncomplete,
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
          'Sprint 2.16B Full Banking Intent Expansion',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 4),
        const Text(
          'Collect real Samsung A55 landmarks for the remaining 36 banking '
          'intents: 25 samples each, 900 new samples total. Only landmark '
          'JSON is stored locally; raw video is not saved.',
        ),
        const SizedBox(height: 8),
        Text(
          statusMessage,
          style: TextStyle(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _OverallProgressCard extends StatelessWidget {
  const _OverallProgressCard({
    required this.selectedLabel,
    required this.selectedCount,
    required this.totalSamples,
    required this.completedLabels,
  });

  final String selectedLabel;
  final int selectedCount;
  final int totalSamples;
  final int completedLabels;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Collection Progress',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            _StatusRow(label: 'Selected label', value: selectedLabel),
            _StatusRow(
              label: 'Selected progress',
              value: '$selectedCount / ${PhoneDatasetScope.samplesPerLabel}',
            ),
            _StatusRow(
              label: 'Overall progress',
              value: '$totalSamples / ${PhoneDatasetScope.newSampleTarget}',
            ),
            _StatusRow(
              label: 'Completed labels',
              value: '$completedLabels / 36',
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: totalSamples / PhoneDatasetScope.newSampleTarget,
            ),
          ],
        ),
      ),
    );
  }
}

class _PilotSummaryCard extends StatelessWidget {
  const _PilotSummaryCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Sprint 2.16A Completed (Protected)',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            for (final label in PhoneSampleStore.sprint216APilotLabels)
              _StatusRow(label: label, value: '25 / 25'),
            const SizedBox(height: 4),
            Text(
              'These labels are not selectable or deletable from this page.',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
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
      child: AspectRatio(
        key: PhoneDatasetCollectionPage.cameraPreviewKey,
        // Match the proven portrait preview used by Live Camera Prototype.
        aspectRatio: PhoneDatasetCollectionPage.cameraPreviewAspectRatio,
        child: preview,
      ),
    );
  }
}

class _LabelSelector extends StatefulWidget {
  const _LabelSelector({
    required this.selectedLabel,
    required this.counts,
    required this.onChanged,
    required this.onSelectNext,
  });

  final String selectedLabel;
  final Map<String, int> counts;
  final ValueChanged<String>? onChanged;
  final VoidCallback? onSelectNext;

  @override
  State<_LabelSelector> createState() => _LabelSelectorState();
}

class _LabelSelectorState extends State<_LabelSelector> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final labels = PhoneSampleStore.sprint216BCollectionLabels
        .where((label) => label.toLowerCase().contains(_query.toLowerCase()))
        .toList(growable: false);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Remaining Banking Intent',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text(
              '${PhoneSampleStore.sprint216BCollectionLabels.length} selectable '
              'labels, ${PhoneDatasetScope.samplesPerLabel} samples each',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              onChanged: (value) => setState(() => _query = value.trim()),
              decoration: const InputDecoration(
                labelText: 'Search banking labels',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: widget.onSelectNext,
              icon: const Icon(Icons.skip_next),
              label: const Text('Select Next Incomplete'),
            ),
            const SizedBox(height: 10),
            if (labels.isEmpty)
              const Text('No banking labels match this search.'),
            for (final label in labels) ...[
              _LabelOption(
                label: label,
                count: widget.counts[label] ?? 0,
                selected: widget.selectedLabel == label,
                onTap: widget.onChanged == null
                    ? null
                    : () => widget.onChanged!(label),
              ),
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
    final remaining = (PhoneDatasetScope.samplesPerLabel - count).clamp(
      0,
      PhoneDatasetScope.samplesPerLabel,
    );
    final completed = remaining == 0;
    final enabled = onTap != null;
    final backgroundColor = selected
        ? colorScheme.primaryContainer
        : completed
        ? colorScheme.secondaryContainer
        : colorScheme.surfaceContainerHigh;
    final activeForeground = selected
        ? colorScheme.onPrimaryContainer
        : completed
        ? colorScheme.onSecondaryContainer
        : colorScheme.onSurface;
    final activeSupporting = selected
        ? colorScheme.onPrimaryContainer
        : completed
        ? colorScheme.onSecondaryContainer
        : colorScheme.onSurfaceVariant;
    final foregroundColor = enabled
        ? activeForeground
        : colorScheme.onSurface.withValues(alpha: 0.38);
    final supportingColor = enabled
        ? activeSupporting
        : colorScheme.onSurface.withValues(alpha: 0.38);
    final borderColor = selected
        ? colorScheme.primary
        : completed
        ? colorScheme.secondary
        : colorScheme.outlineVariant;

    return Material(
      key: ValueKey('collection-label-$label'),
      color: backgroundColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: enabled
              ? borderColor
              : colorScheme.outlineVariant.withValues(alpha: 0.5),
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
                completed
                    ? Icons.check_circle
                    : selected
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
                color: supportingColor,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: foregroundColor,
                  ),
                ),
              ),
              Text(
                '$count / ${PhoneDatasetScope.samplesPerLabel}',
                style: TextStyle(color: foregroundColor),
              ),
              const SizedBox(width: 8),
              Text(
                remaining == 0 ? 'done' : '$remaining left',
                style: TextStyle(color: supportingColor),
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
              label: 'Left slot',
              value: frame?.leftDetected == true ? 'Detected' : 'Zeros',
            ),
            _StatusRow(
              label: 'Right slot',
              value: frame?.rightDetected == true ? 'Detected' : 'Zeros',
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
    required this.selectedLabelComplete,
    required this.onStartCamera,
    required this.onStartCapture,
    required this.onResetCapture,
    required this.onStopCamera,
    required this.onDeleteLastSample,
  });

  final bool isCameraStarting;
  final bool isCameraStarted;
  final bool isCapturing;
  final bool isSaving;
  final bool selectedLabelComplete;
  final VoidCallback onStartCamera;
  final VoidCallback onStartCapture;
  final VoidCallback onResetCapture;
  final VoidCallback onStopCamera;
  final VoidCallback onDeleteLastSample;

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
              onPressed: disabled || !isCameraStarted || selectedLabelComplete
                  ? null
                  : onStartCapture,
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
            OutlinedButton.icon(
              onPressed: disabled || !isCameraStarted ? null : onStopCamera,
              icon: const Icon(Icons.videocam_off),
              label: const Text('Stop Camera'),
            ),
            TextButton.icon(
              onPressed: disabled ? null : onDeleteLastSample,
              icon: const Icon(Icons.delete_outline),
              label: const Text('Delete Last Saved Sample'),
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
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: colorScheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline, color: colorScheme.onErrorContainer),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: TextStyle(color: colorScheme.onErrorContainer),
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
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.lock_outline,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 8),
            const Expanded(
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
