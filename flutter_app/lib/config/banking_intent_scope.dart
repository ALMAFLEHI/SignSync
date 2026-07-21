class BankingIntentScope {
  static const List<String> frozenIntents = <String>[
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

  static const List<String> removedIntents = <String>[
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
    if (frozenIntents.length != 40 || frozenIntents.toSet().length != 40) {
      throw StateError(
        'The final banking scope must contain 40 unique intents.',
      );
    }
    if (frozenIntents.any(removedIntents.contains)) {
      throw StateError('Removed banking intents cannot enter the final scope.');
    }
    if (frozenIntents.any((id) => RegExp(r'^[A-Z0-9]$').hasMatch(id))) {
      throw StateError(
        'Alphabet and digit labels are not final banking intents.',
      );
    }
  }
}
