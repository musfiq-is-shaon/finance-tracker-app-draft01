enum LoanActivityType {
  given,      // You gave money to them (they owe you)
  borrowed,   // You borrowed money from them (you owe them)
  paymentReceived, // They paid you back
  paymentMade,    // You paid them
}

extension LoanActivityTypeExtension on LoanActivityType {
  String get displayName {
    switch (this) {
      case LoanActivityType.given:
        return 'Loan Given';
      case LoanActivityType.borrowed:
        return 'Loan Taken';
      case LoanActivityType.paymentReceived:
        return 'Payment Received';
      case LoanActivityType.paymentMade:
        return 'Payment Made';
    }
  }

  String get apiValue {
    switch (this) {
      case LoanActivityType.given:
        return 'given';
      case LoanActivityType.borrowed:
        return 'borrowed';
      case LoanActivityType.paymentReceived:
        return 'payment_received';
      case LoanActivityType.paymentMade:
        return 'payment_made';
    }
  }

  static LoanActivityType fromString(String value) {
    switch (value) {
      case 'given':
        return LoanActivityType.given;
      case 'borrowed':
        return LoanActivityType.borrowed;
      case 'payment_received':
        return LoanActivityType.paymentReceived;
      case 'payment_made':
        return LoanActivityType.paymentMade;
      default:
        return LoanActivityType.given;
    }
  }
}

class LoanActivity {
  final String id;
  final String userId;
  final String contactId;
  final LoanActivityType activityType;
  final double amount;
  final double balanceAfter;
  final String? description;
  final DateTime activityDate;
  final DateTime createdAt;
  final DateTime updatedAt;

  LoanActivity({
    required this.id,
    required this.userId,
    required this.contactId,
    required this.activityType,
    required this.amount,
    required this.balanceAfter,
    this.description,
    required this.activityDate,
    required this.createdAt,
    required this.updatedAt,
  });

  factory LoanActivity.fromJson(Map<String, dynamic> json) {
    return LoanActivity(
      id: json['id'].toString(), // Convert int to String
      userId: json['user_id'].toString(), // Convert int to String
      contactId: json['contact_id'].toString(), // Convert int to String
      activityType: LoanActivityTypeExtension.fromString(json['activity_type'] as String),
      amount: (json['amount'] as num).toDouble(),
      balanceAfter: (json['balance_after'] as num).toDouble(),
      description: json['description'] as String?,
      activityDate: DateTime.parse(json['activity_date'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'contact_id': contactId,
      'activity_type': activityType.apiValue,
      'amount': amount,
      'balance_after': balanceAfter,
      'description': description,
      'activity_date': activityDate.toIso8601String().split('T')[0],
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  LoanActivity copyWith({
    String? id,
    String? userId,
    String? contactId,
    LoanActivityType? activityType,
    double? amount,
    double? balanceAfter,
    String? description,
    DateTime? activityDate,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return LoanActivity(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      contactId: contactId ?? this.contactId,
      activityType: activityType ?? this.activityType,
      amount: amount ?? this.amount,
      balanceAfter: balanceAfter ?? this.balanceAfter,
      description: description ?? this.description,
      activityDate: activityDate ?? this.activityDate,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

