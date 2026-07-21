import 'dart:collection';

import 'package:flutter/foundation.dart';

import '../models/banking_interaction_session.dart';
import '../models/manual_field_config.dart';
import '../models/query_configuration.dart';

class BankingInteractionController extends ChangeNotifier {
  BankingWorkflowStep _step = BankingWorkflowStep.recognition;
  BankingIntentConfig? _detectedIntent;
  double? _confidence;
  BankingQueryOption? _selectedQuery;
  final Map<String, String> _manualFieldValues = <String, String>{};
  final Map<String, String> _validationErrors = <String, String>{};

  BankingInteractionSession get session => BankingInteractionSession(
    step: _step,
    detectedIntent: _detectedIntent,
    confidence: _confidence,
    selectedQuery: _selectedQuery,
    manualFieldValues: UnmodifiableMapView(_manualFieldValues),
    validationErrors: UnmodifiableMapView(_validationErrors),
  );

  List<ManualFieldConfig> get selectedManualFields {
    final intent = _detectedIntent;
    final query = _selectedQuery;
    if (intent == null || query == null) {
      return const <ManualFieldConfig>[];
    }
    final referencedIds = query.manualFieldIds.toSet();
    return intent.manualFields
        .where((field) => referencedIds.contains(field.id))
        .toList(growable: false);
  }

  List<BankingInteractionDetail> get populatedDetails {
    return selectedManualFields
        .where(
          (field) => (_manualFieldValues[field.id] ?? '').trim().isNotEmpty,
        )
        .map((field) {
          final value = _manualFieldValues[field.id]!.trim();
          return BankingInteractionDetail(
            field: field,
            displayValue: displayValueFor(field, value),
          );
        })
        .toList(growable: false);
  }

  bool get hasManualData =>
      _manualFieldValues.values.any((value) => value.trim().isNotEmpty);

  void acceptPrediction({
    required BankingIntentConfig intent,
    required double confidence,
  }) {
    _detectedIntent = intent;
    _confidence = confidence;
    _selectedQuery = null;
    _manualFieldValues.clear();
    _validationErrors.clear();
    _step = BankingWorkflowStep.confirmation;
    notifyListeners();
  }

  void confirmIntent() {
    if (_detectedIntent == null) {
      return;
    }
    _step = BankingWorkflowStep.querySelection;
    notifyListeners();
  }

  void tryAgain() => reset();

  void selectQuery(BankingQueryOption query) {
    final intent = _detectedIntent;
    if (intent == null || !intent.queries.any((item) => item.id == query.id)) {
      throw ArgumentError(
        'The selected request does not belong to this intent.',
      );
    }
    if (_selectedQuery?.id != query.id) {
      _manualFieldValues.clear();
      _validationErrors.clear();
    }
    _selectedQuery = query;
    notifyListeners();
  }

  bool continueFromQuerySelection() {
    if (_selectedQuery == null) {
      return false;
    }
    _validationErrors.clear();
    _step = selectedManualFields.isEmpty
        ? BankingWorkflowStep.review
        : BankingWorkflowStep.manualDetails;
    notifyListeners();
    return true;
  }

  void updateManualField(String fieldId, String value) {
    if (!selectedManualFields.any((field) => field.id == fieldId)) {
      throw ArgumentError('Unknown manual field: $fieldId.');
    }
    _manualFieldValues[fieldId] = value;
    _validationErrors.remove(fieldId);
    notifyListeners();
  }

  bool submitManualDetails() {
    _validationErrors
      ..clear()
      ..addAll(_validateManualFields());
    if (_validationErrors.isNotEmpty) {
      notifyListeners();
      return false;
    }
    _step = BankingWorkflowStep.review;
    notifyListeners();
    return true;
  }

  void editRequest() {
    _step = BankingWorkflowStep.querySelection;
    notifyListeners();
  }

  void editDetails() {
    _step = selectedManualFields.isEmpty
        ? BankingWorkflowStep.querySelection
        : BankingWorkflowStep.manualDetails;
    notifyListeners();
  }

  void showToBanker() {
    if (_detectedIntent == null || _selectedQuery == null) {
      return;
    }
    _step = BankingWorkflowStep.bankerView;
    notifyListeners();
  }

  bool goBack() {
    switch (_step) {
      case BankingWorkflowStep.recognition:
        return false;
      case BankingWorkflowStep.confirmation:
        reset();
        return true;
      case BankingWorkflowStep.querySelection:
        _step = BankingWorkflowStep.confirmation;
        notifyListeners();
        return true;
      case BankingWorkflowStep.manualDetails:
        _step = BankingWorkflowStep.querySelection;
        notifyListeners();
        return true;
      case BankingWorkflowStep.review:
        _step = selectedManualFields.isEmpty
            ? BankingWorkflowStep.querySelection
            : BankingWorkflowStep.manualDetails;
        notifyListeners();
        return true;
      case BankingWorkflowStep.bankerView:
        _step = BankingWorkflowStep.review;
        notifyListeners();
        return true;
    }
  }

  void reset({bool notify = true}) {
    _step = BankingWorkflowStep.recognition;
    _detectedIntent = null;
    _confidence = null;
    _selectedQuery = null;
    _manualFieldValues.clear();
    _validationErrors.clear();
    if (notify) {
      notifyListeners();
    }
  }

  String displayValueFor(ManualFieldConfig field, String value) {
    if (!field.displayMasked || value.isEmpty) {
      return value;
    }
    if (value.length <= 4) {
      return List<String>.filled(value.length, '*').join();
    }
    return '**** ${value.substring(value.length - 4)}';
  }

  Map<String, String> _validateManualFields() {
    final errors = <String, String>{};
    for (final field in selectedManualFields) {
      final value = (_manualFieldValues[field.id] ?? '').trim();
      if (field.required && value.isEmpty) {
        errors[field.id] = 'Please complete the required field.';
        continue;
      }
      if (value.isEmpty) {
        continue;
      }
      if (field.maximumLength != null && value.length > field.maximumLength!) {
        errors[field.id] =
            'Use no more than ${field.maximumLength} characters.';
        continue;
      }
      switch (field.type) {
        case ManualFieldType.number:
        case ManualFieldType.maskedNumber:
          if (!RegExp(r'^\d+$').hasMatch(value)) {
            errors[field.id] = 'Enter numbers only.';
          }
          break;
        case ManualFieldType.amount:
          final parsed = double.tryParse(value);
          if (!RegExp(r'^\d+(\.\d{1,2})?$').hasMatch(value) ||
              parsed == null ||
              parsed <= 0) {
            errors[field.id] = 'Enter a valid amount using up to two decimals.';
          }
          break;
        case ManualFieldType.date:
          if (!_isValidDate(value)) {
            errors[field.id] = 'Choose a valid date.';
          }
          break;
        case ManualFieldType.time:
          if (!_isValidTime(value)) {
            errors[field.id] = 'Choose a valid time.';
          }
          break;
        case ManualFieldType.select:
          if (!field.options.contains(value)) {
            errors[field.id] = 'Choose one of the available options.';
          }
          break;
        case ManualFieldType.text:
        case ManualFieldType.multilineText:
          break;
      }
    }
    return errors;
  }

  bool _isValidDate(String value) {
    final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(value);
    if (match == null) {
      return false;
    }
    final year = int.parse(match.group(1)!);
    final month = int.parse(match.group(2)!);
    final day = int.parse(match.group(3)!);
    final parsed = DateTime(year, month, day);
    return parsed.year == year && parsed.month == month && parsed.day == day;
  }

  bool _isValidTime(String value) {
    final match = RegExp(r'^(\d{2}):(\d{2})$').firstMatch(value);
    if (match == null) {
      return false;
    }
    final hour = int.parse(match.group(1)!);
    final minute = int.parse(match.group(2)!);
    return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59;
  }

  @override
  void dispose() {
    _manualFieldValues.clear();
    _validationErrors.clear();
    super.dispose();
  }
}
