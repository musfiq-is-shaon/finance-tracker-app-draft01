class LoanContact {
  final String id;
  final String userId;
  final String name;
  final String? phoneNumber;
  final String? email;
  final double initialBalance;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;
  final double currentBalance;
  final int activityCount;

  LoanContact({
    required this.id,
    required this.userId,
    required this.name,
    this.phoneNumber,
    this.email,
    this.initialBalance = 0,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
    this.currentBalance = 0,
    this.activityCount = 0,
  });

  /// Positive balance = they owe you
  /// Negative balance = you owe them
  bool get isOwedMoney => currentBalance > 0;
  bool get owesMoney => currentBalance < 0;
  bool get isSettled => currentBalance == 0;

  factory LoanContact.fromJson(Map<String, dynamic> json) {
    return LoanContact(
      id: json['id'].toString(), // Convert int to String
      userId: json['user_id'].toString(), // Convert int to String
      name: json['name'] as String,
      phoneNumber: json['phone_number'] as String?,
      email: json['email'] as String?,
      initialBalance: (json['initial_balance'] as num?)?.toDouble() ?? 0,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      currentBalance: (json['current_balance'] as num?)?.toDouble() ?? 0,
      activityCount: json['activity_count'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'phone_number': phoneNumber,
      'email': email,
      'initial_balance': initialBalance,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'current_balance': currentBalance,
      'activity_count': activityCount,
    };
  }

  LoanContact copyWith({
    String? id,
    String? userId,
    String? name,
    String? phoneNumber,
    String? email,
    double? initialBalance,
    String? notes,
    DateTime? createdAt,
    DateTime? updatedAt,
    double? currentBalance,
    int? activityCount,
  }) {
    return LoanContact(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      email: email ?? this.email,
      initialBalance: initialBalance ?? this.initialBalance,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      currentBalance: currentBalance ?? this.currentBalance,
      activityCount: activityCount ?? this.activityCount,
    );
  }
}

