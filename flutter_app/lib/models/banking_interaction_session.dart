import 'manual_field_config.dart';
import 'query_configuration.dart';

enum BankingWorkflowStep {
  recognition,
  confirmation,
  querySelection,
  manualDetails,
  review,
  bankerView,
}

class BankingInteractionDetail {
  const BankingInteractionDetail({
    required this.field,
    required this.displayValue,
  });

  final ManualFieldConfig field;
  final String displayValue;
}

class BankingInteractionSession {
  const BankingInteractionSession({
    required this.step,
    required this.detectedIntent,
    required this.confidence,
    required this.selectedQuery,
    required this.manualFieldValues,
    required this.validationErrors,
  });

  factory BankingInteractionSession.empty() {
    return const BankingInteractionSession(
      step: BankingWorkflowStep.recognition,
      detectedIntent: null,
      confidence: null,
      selectedQuery: null,
      manualFieldValues: <String, String>{},
      validationErrors: <String, String>{},
    );
  }

  final BankingWorkflowStep step;
  final BankingIntentConfig? detectedIntent;
  final double? confidence;
  final BankingQueryOption? selectedQuery;
  final Map<String, String> manualFieldValues;
  final Map<String, String> validationErrors;

  bool get hasActiveData {
    return detectedIntent != null ||
        selectedQuery != null ||
        manualFieldValues.values.any((value) => value.trim().isNotEmpty);
  }
}
