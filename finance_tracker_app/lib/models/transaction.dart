class Transaction {
  final String id;
  final String userId;
  final String type; // 'income' or 'expense'
  final double amount;
  final String category;
  final String description;
  final DateTime date;
  final DateTime createdAt;

  Transaction({
    required this.id,
    required this.userId,
    required this.type,
    required this.amount,
    required this.category,
    required this.description,
    required this.date,
    required this.createdAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'].toString(), // Convert int to String
      userId: json['user_id'].toString(), // Convert int to String
      type: json['type'] as String,
      amount: (json['amount'] as num).toDouble(),
      category: json['category'] as String,
      description: json['description'] as String? ?? '',
      date: DateTime.parse(json['date'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'type': type,
      'amount': amount,
      'category': category,
      'description': description,
      'date': date.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
    };
  }

  Transaction copyWith({
    String? id,
    String? userId,
    String? type,
    double? amount,
    String? category,
    String? description,
    DateTime? date,
    DateTime? createdAt,
  }) {
    return Transaction(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      amount: amount ?? this.amount,
      category: category ?? this.category,
      description: description ?? this.description,
      date: date ?? this.date,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

