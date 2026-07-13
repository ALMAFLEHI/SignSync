class PhoneDatasetScope {
  static const String sprintId = '2.16B';
  static const String participantId = 'P02_PHONE';
  static const int samplesPerLabel = 25;
  static const int newSampleTarget = 900;
  static const int finalBankingPhoneTarget = 1000;

  static const List<String> sprint216APilotIntents = <String>[
    'transfer',
    'document',
    'signature',
    'atm',
  ];

  static const List<String> sprint216BRemainingBankingIntents = <String>[
    'deposit',
    'withdraw',
    'balance',
    'account',
    'card',
    'pin',
    'password',
    'identity_verification',
    'cash',
    'payment',
    'fee',
    'loan',
    'savings',
    'open_account',
    'close_account',
    'fraud',
    'block_card',
    'help',
    'confirm',
    'statement',
    'bill_payment',
    'branch',
    'cheque',
    'interest_rate',
    'credit_card',
    'debit_card',
    'lost_card',
    'replace_card',
    'change_pin',
    'reset_password',
    'refund',
    'complaint',
    'appointment',
    'account_number',
    'card_limit',
    'daily_limit',
  ];

  static const List<String> activeBankingIntentsV3 = <String>[
    'deposit',
    'withdraw',
    'balance',
    'transfer',
    'account',
    'card',
    'pin',
    'password',
    'identity_verification',
    'cash',
    'payment',
    'fee',
    'loan',
    'savings',
    'open_account',
    'close_account',
    'fraud',
    'block_card',
    'help',
    'confirm',
    'statement',
    'document',
    'bill_payment',
    'atm',
    'branch',
    'cheque',
    'interest_rate',
    'credit_card',
    'debit_card',
    'lost_card',
    'replace_card',
    'change_pin',
    'reset_password',
    'refund',
    'signature',
    'complaint',
    'appointment',
    'account_number',
    'card_limit',
    'daily_limit',
  ];

  static const List<String> removedBankingIntents = <String>[
    'online_banking',
    'mobile_banking',
    'currency_exchange',
    'exchange_rate',
    'fixed_deposit',
    'customer_service',
    'update_details',
    'phone_number',
    'email_address',
    'address_change',
  ];

  static void validate() {
    if (sprint216APilotIntents.length != 4 ||
        sprint216APilotIntents.toSet().length != 4) {
      throw StateError('Sprint 2.16A pilot scope must contain four labels.');
    }
    if (sprint216BRemainingBankingIntents.length != 36 ||
        sprint216BRemainingBankingIntents.toSet().length != 36) {
      throw StateError('Sprint 2.16B scope must contain 36 unique labels.');
    }
    if (sprint216BRemainingBankingIntents.any(
      sprint216APilotIntents.contains,
    )) {
      throw StateError('Pilot and remaining collection scopes overlap.');
    }
    final expectedRemaining = activeBankingIntentsV3
        .where((label) => !sprint216APilotIntents.contains(label))
        .toList(growable: false);
    if (!_sameOrder(expectedRemaining, sprint216BRemainingBankingIntents)) {
      throw StateError('Sprint 2.16B must preserve active V3 order.');
    }
    if (sprint216BRemainingBankingIntents.any(removedBankingIntents.contains)) {
      throw StateError('Removed labels cannot appear in Sprint 2.16B.');
    }
    if (sprint216BRemainingBankingIntents.any(
      (label) => RegExp(r'^[A-Z0-9]$').hasMatch(label),
    )) {
      throw StateError('Sprint 2.16B cannot include alphabet or digit labels.');
    }
    if (samplesPerLabel * sprint216BRemainingBankingIntents.length !=
            newSampleTarget ||
        newSampleTarget + samplesPerLabel * sprint216APilotIntents.length !=
            finalBankingPhoneTarget) {
      throw StateError('Sprint 2.16B target arithmetic is invalid.');
    }
  }

  static bool _sameOrder(List<String> left, List<String> right) {
    if (left.length != right.length) {
      return false;
    }
    for (var index = 0; index < left.length; index += 1) {
      if (left[index] != right[index]) {
        return false;
      }
    }
    return true;
  }
}
