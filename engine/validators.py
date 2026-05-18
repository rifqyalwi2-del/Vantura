"""
engine/validators.py
Input validation with user-friendly messages.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    valid:  bool = True
    errors: list[str] = field(default_factory=list)

    def add(self, msg: str):
        self.errors.append(msg)
        self.valid = False


def validate_profile_inputs(
    current_age:    int,
    retirement_age: int,
    monthly_salary: float,
    current_savings:float,
    savings_rate:   float,
    sandwich:       float,
) -> ValidationResult:
    r = ValidationResult()

    if not (18 <= current_age <= 75):
        r.add("Usia saat ini harus antara 18–75 tahun.")
    if retirement_age <= current_age:
        r.add("Usia pensiun harus lebih besar dari usia saat ini.")
    if retirement_age > 80:
        r.add("Usia pensiun maksimal 80 tahun.")
    if (retirement_age - current_age) < 1:
        r.add("Minimal 1 tahun sebelum pensiun.")
    if monthly_salary < 0:
        r.add("Gaji tidak boleh negatif.")
    if monthly_salary == 0:
        r.add("Gaji/penghasilan bulanan wajib diisi (> Rp 0).")
    if current_savings < 0:
        r.add("Tabungan tidak boleh negatif.")
    if not (0 <= savings_rate <= 100):
        r.add("Persentase menabung harus antara 0–100%.")
    if sandwich < 0:
        r.add("Beban sandwich generation tidak boleh negatif.")
    if sandwich >= monthly_salary:
        r.add("Beban sandwich melebihi gaji — harap periksa kembali.")

    return r