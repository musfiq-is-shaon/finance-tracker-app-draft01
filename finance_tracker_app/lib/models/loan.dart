class Loan {
  final String id;
  final String userId;
  final String type; // 'given' or 'borrowed'
  final String personName;
  final String? phoneNumber;
  final double amount;
  final double? paidAmount;
  final String? description;
  final DateTime date;
  final bool isPaid;
  final DateTime createdAt;

  Loan({
    required this.id,
    required this.userId,
    required this.type,
    required this.personName,
    this.phoneNumber,
    required this.amount,
    this.paidAmount,
    this.description,
    required this.date,
    required this.isPaid,
    required this.createdAt,
  });

  double get outstandingAmount => amount - (paidAmount ?? 0);

  factory Loan.fromJson(Map<String, dynamic> json) {
    return Loan(
      id: json['id'].toString(), // Convert int to String
      userId: json['user_id'].toString(), // Convert int to String
      type: json['type'] as String,
      personName: json['person_name'] as String,
      phoneNumber: json['phone_number'] as String?,
      amount: (json['amount'] as num).toDouble(),
      paidAmount: json['paid_amount'] != null ? (json['paid_amount'] as num).toDouble() : null,
      description: json['description'] as String?,
      date: DateTime.parse(json['date'] as String),
      isPaid: json['is_paid'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'type': type,
      'person_name': personName,
      'phone_number': phoneNumber,
      'amount': amount,
      'paid_amount': paidAmount,
      'description': description,
      'date': date.toIso8601String(),
      'is_paid': isPaid,
      'created_at': createdAt.toIso8601String(),
    };
  }

  Loan copyWith({
    String? id,
    String? userId,
    String? type,
    String? personName,
    String? phoneNumber,
    double? amount,
    double? paidAmount,
    String? description,
    DateTime? date,
    bool? isPaid,
    DateTime? createdAt,
  }) {
    return Loan(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      personName: personName ?? this.personName,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      amount: amount ?? this.amount,
      paidAmount: paidAmount ?? this.paidAmount,
      description: description ?? this.description,
      date: date ?? this.date,
      isPaid: isPaid ?? this.isPaid,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

