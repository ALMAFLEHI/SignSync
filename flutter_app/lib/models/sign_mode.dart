enum SignMode { alphabet, number, bankingIntent }

extension SignModeLabel on SignMode {
  String get displayName {
    switch (this) {
      case SignMode.alphabet:
        return 'Alphabet Mode';
      case SignMode.number:
        return 'Number Mode';
      case SignMode.bankingIntent:
        return 'Banking Intent Mode';
    }
  }

  String get description {
    switch (this) {
      case SignMode.alphabet:
        return 'A-Z only';
      case SignMode.number:
        return 'Digits 0-9 only';
      case SignMode.bankingIntent:
        return 'Banking intent labels only';
    }
  }
}
