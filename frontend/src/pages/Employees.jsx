import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import StatusBadge from "../components/StatusBadge";
import PageHeader from "../components/PageHeader";
import CreateEmployeeForm from "../components/employees/CreateEmployeeForm";
import EditEmployeeForm from "../components/employees/EditEmployeeForm";
import AccountForm from "../components/employees/AccountForm";
import BalanceEditor from "../components/employees/BalanceEditor";
import {
  EMPTY_FORM,
  EMPTY_EDIT_FORM,
  EMPTY_ACCOUNT_FORM,
} from "../components/employees/constants";
import { getErrorMessage } from "../utils/errorMessage";
import { formatLeaveType } from "../utils/formatters";

function Employees() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState(EMPTY_FORM);

  const [editingEmployee, setEditingEmployee] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY_EDIT_FORM);

  const [accountEmployee, setAccountEmployee] = useState(null);
  const [accountForm, setAccountForm] = useState(EMPTY_ACCOUNT_FORM);

  const [accountSubmitting, setAccountSubmitting] = useState(false);

  const [balanceEmployee, setBalanceEmployee] = useState(null);
  const [balances, setBalances] = useState([]);
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [balanceUpdating, setBalanceUpdating] = useState(null);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");

  const [page, setPage] = useState(1);
  const limit = 10;
  const [totalPages, setTotalPages] = useState(0);
  const [totalEmployees, setTotalEmployees] = useState(0);

  const fetchEmployees = useCallback(async (
    pageNumber = 1,
    searchOverride = search
  ) => {
    try {
      setLoading(true);
      setLoadError("");

      const params = {
        page: pageNumber,
        limit,
      };

      if (searchOverride.trim()) {
        params.search = searchOverride.trim();
      }

      if (statusFilter) {
        params.status = statusFilter;
      }

      if (departmentFilter.trim()) {
        params.department = departmentFilter.trim();
      }

      const response = await api.get("/employees", {
        params,
      });

      setEmployees(response.data.items);
      setTotalPages(response.data.pages);
      setTotalEmployees(response.data.total);
      setPage(response.data.page);
    } catch (error) {
      setLoadError(
        getErrorMessage(error, "Unable to load employees.")
      );
    } finally {
      setLoading(false);
    }
  }, [departmentFilter, limit, search, statusFilter]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchEmployees(page);
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchEmployees, page]);

  const handleSearch = () => {
    const trimmedSearch = searchInput.trim();

    setSearch(trimmedSearch);

    if (page !== 1) {
      setPage(1);
    } else {
      fetchEmployees(1, trimmedSearch);
    }
  };

  const handleClearFilters = () => {
    setSearchInput("");
    setSearch("");
    setStatusFilter("");
    setDepartmentFilter("");

    if (page !== 1) {
      setPage(1);
    } else {
      fetchEmployees(1, "");
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  };

  const handleCreate = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");
    setSubmitting(true);

    try {
      await api.post("/employees", {
        employee_number: Number(form.employee_number),
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        department: form.department,
        position: form.position,
        date_hired: form.date_hired,
        status: form.status,
      });

      setMessage("Employee created successfully.");

      setForm(EMPTY_FORM);

      setShowForm(false);

      await fetchEmployees();
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to create employee.")
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditClick = (employee) => {
    setEditingEmployee(employee);

    setEditForm({
      first_name: employee.first_name,
      last_name: employee.last_name,
      email: employee.email,
      department: employee.department,
      position: employee.position,
      status: employee.status,
    });

    setError("");
    setMessage("");
  };

  const handleEditChange = (event) => {
    const { name, value } = event.target;

    setEditForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  };

  const handleUpdate = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");

    const changedFields = {};

    const editableFields = [
      "first_name",
      "last_name",
      "email",
      "department",
      "position",
      "status",
    ];

    editableFields.forEach((field) => {
      if (editForm[field] !== editingEmployee[field]) {
        changedFields[field] = editForm[field];
      }
    });

    if (Object.keys(changedFields).length === 0) {
      setMessage("No changes were made.");
      return;
    }

    try {
      await api.patch(
        `/employees/${editingEmployee.id}`,
        changedFields
      );

      setMessage("Employee updated successfully.");
      setEditingEmployee(null);

      await fetchEmployees();
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to update employee.")
      );
    }
  };

  const handleDeactivate = async (employee) => {
    const confirmed = window.confirm(
      `Deactivate ${employee.first_name} ${employee.last_name}?`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setMessage("");

    try {
      await api.delete(`/employees/${employee.id}`);

      setMessage("Employee deactivated successfully.");

      await fetchEmployees();
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to deactivate employee.")
      );
    }
  };

  const handleAccountChange = (event) => {
    const { name, value } = event.target;

    setAccountForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  };

  const handleAccountClick = (employee) => {
    setAccountEmployee(employee);

    setAccountForm({
      email: employee.email,
      password: "",
    });

    setError("");
    setMessage("");
  };

  const handleCreateAccount = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");
    setAccountSubmitting(true);

    try {
      await api.post(
        `/employees/${accountEmployee.id}/account`,
        {
          email: accountForm.email,
          password: accountForm.password,
        }
      );

      setMessage("Employee account created successfully.");

      setAccountEmployee(null);

      setAccountForm(EMPTY_ACCOUNT_FORM);

      await fetchEmployees();
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to create employee account.")
      );
    } finally {
      setAccountSubmitting(false);
    }
  };

  const handleBalanceClick = async (employee) => {
    setBalanceEmployee(employee);
    setBalances([]);
    setBalanceLoading(true);

    setError("");
    setMessage("");

    try {
      const response = await api.get(
        `/leaves/balance/${employee.id}`
      );

      setBalances(response.data);
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to load leave balances.")
      );
      setBalanceEmployee(null);
    } finally {
      setBalanceLoading(false);
    }
  };

  const handleBalanceChange = (leaveType, value) => {
    setBalances((currentBalances) =>
      currentBalances.map((balance) =>
        balance.leave_type === leaveType
          ? {
              ...balance,
              total_days: value,
              remaining_days:
                Number(value) - balance.used_days,
            }
          : balance
      )
    );
  };

  const handleBalanceUpdate = async (balance) => {
    setError("");
    setMessage("");
    setBalanceUpdating(balance.leave_type);

    try {
      const response = await api.patch(
        `/leaves/balance/${balanceEmployee.id}/${balance.leave_type}`,
        {
          total_days: Number(balance.total_days),
        }
      );

      setBalances((currentBalances) =>
        currentBalances.map((currentBalance) =>
          currentBalance.leave_type ===
          balance.leave_type
            ? response.data
            : currentBalance
        )
      );

      setMessage(
        `${formatLeaveType(
          balance.leave_type
        )} balance updated successfully.`
      );
    } catch (error) {
      setError(
        getErrorMessage(error, "Unable to update leave balance.")
      );
    } finally {
      setBalanceUpdating(null);
    }
  };

  const hasActiveFilters = Boolean(
    search.trim() || statusFilter.trim() || departmentFilter.trim()
  );

  const toggleAddForm = () => {
    setShowForm((current) => !current);
    setError("");
    setMessage("");
  };

  return (
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="Employees"
          subtitle="Manage employee records and account access."
        >
          <button
            className={showForm ? "btn-secondary" : "btn-primary"}
            type="button"
            onClick={toggleAddForm}
          >
            {showForm ? "Cancel" : "Add Employee"}
          </button>
        </PageHeader>

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        {showForm && (
          <CreateEmployeeForm
            form={form}
            submitting={submitting}
            onChange={handleChange}
            onSubmit={handleCreate}
          />
        )}

        {editingEmployee && (
          <EditEmployeeForm
            employee={editingEmployee}
            form={editForm}
            onChange={handleEditChange}
            onSubmit={handleUpdate}
            onCancel={() => setEditingEmployee(null)}
          />
        )}

        {accountEmployee && (
          <AccountForm
            employee={accountEmployee}
            form={accountForm}
            submitting={accountSubmitting}
            onChange={handleAccountChange}
            onSubmit={handleCreateAccount}
            onCancel={() => setAccountEmployee(null)}
          />
        )}

        {balanceEmployee && (
          <BalanceEditor
            employee={balanceEmployee}
            balances={balances}
            loading={balanceLoading}
            updatingType={balanceUpdating}
            onBalanceChange={handleBalanceChange}
            onBalanceUpdate={handleBalanceUpdate}
            onClose={() => setBalanceEmployee(null)}
          />
        )}

        <section>
          <div className="toolbar">
            <input
              type="text"
              placeholder="Search name, employee number, or email..."
              value={searchInput}
              onChange={(event) =>
                setSearchInput(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
            />
            <button
              className="btn-secondary"
              type="button"
              onClick={handleSearch}
            >
              Search
            </button>

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value)
              }
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="resigned">Resigned</option>
              <option value="terminated">Terminated</option>
            </select>

            <input
              type="text"
              placeholder="Department"
              value={departmentFilter}
              onChange={(event) =>
                setDepartmentFilter(event.target.value)
              }
            />

            <button
              className="btn-secondary"
              type="button"
              onClick={handleClearFilters}
            >
              Clear Filters
            </button>
          </div>

          <p className="results-line">
            Showing {employees.length} of {totalEmployees} employees
          </p>

          {loading ? (
            <Loading message="Loading employees..." />
          ) : loadError ? (
            <ErrorState
              message={loadError}
              onRetry={() => fetchEmployees(page)}
            />
          ) : employees.length === 0 ? (
            <EmptyState
              message={
                hasActiveFilters
                  ? "No employees match your search or filters."
                  : "No employees have been added yet."
              }
            />
          ) : (
            <div className="responsive-table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Employee #</th>
                      <th>Email</th>
                      <th>Department</th>
                      <th>Position</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>

                  <tbody>
                    {employees.map((employee) => (
                      <tr key={employee.id}>
                        <td data-label="Employee">
                          <span className="responsive-cell-value responsive-name">
                            {employee.first_name}{" "}
                            {employee.last_name}
                          </span>
                        </td>

                        <td data-label="Employee #">
                          <span className="responsive-cell-value">
                            {employee.employee_number}
                          </span>
                        </td>

                        <td data-label="Email" className="text-cell">
                          <span className="responsive-cell-value">
                            {employee.email}
                          </span>
                        </td>

                        <td data-label="Department" className="text-cell">
                          <span className="responsive-cell-value">
                            {employee.department}
                          </span>
                        </td>

                        <td data-label="Position" className="text-cell">
                          <span className="responsive-cell-value">
                            {employee.position}
                          </span>
                        </td>

                        <td data-label="Status">
                          <span className="responsive-cell-value">
                            <StatusBadge status={employee.status} />
                          </span>
                        </td>

                        <td data-label="Actions" className="action-cell">
                          <button
                            className="icon-button"
                            type="button"
                            title="Edit employee"
                            aria-label={`Edit ${employee.first_name} ${employee.last_name}`}
                            onClick={() =>
                              handleEditClick(employee)
                            }
                          >
                            <span className="material-symbols-outlined">
                              edit
                            </span>
                          </button>

                          <button
                            className="icon-button"
                            type="button"
                            title="Manage leave balances"
                            aria-label={`Manage leave balances for ${employee.first_name} ${employee.last_name}`}
                            onClick={() =>
                              handleBalanceClick(employee)
                            }
                          >
                            <span className="material-symbols-outlined">
                              account_balance_wallet
                            </span>
                          </button>

                          {employee.has_account === false && (
                            <button
                              className="icon-button icon-button-success"
                              type="button"
                              title="Create employee account"
                              aria-label={`Create account for ${employee.first_name} ${employee.last_name}`}
                              onClick={() =>
                                handleAccountClick(employee)
                              }
                            >
                              <span className="material-symbols-outlined">
                                person_add
                              </span>
                            </button>
                          )}

                          {employee.status === "active" && (
                            <button
                              className="icon-button icon-button-danger"
                              type="button"
                              title="Deactivate employee"
                              aria-label={`Deactivate ${employee.first_name} ${employee.last_name}`}
                              onClick={() =>
                                handleDeactivate(employee)
                              }
                            >
                              <span className="material-symbols-outlined">
                                person_off
                              </span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="toolbar">
            <button
              className="btn-secondary"
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
            >
              Previous
            </button>

            <span className="results-line">
              {" "}
              Page {page} of {totalPages}{" "}
            </span>

            <button
              className="btn-secondary"
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </button>
          </div>
        </section>
      </main>
    </AppShell>
  );
}

export default Employees;
