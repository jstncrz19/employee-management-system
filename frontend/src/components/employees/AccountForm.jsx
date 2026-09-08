function AccountForm({ employee, form, submitting, onChange, onSubmit, onCancel }) {
  return (
    <section>
      <h2>
        Create Account for{" "}
        {employee.first_name}{" "}
        {employee.last_name}
      </h2>

      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="account-email">
            Email
          </label>

          <input
            id="account-email"
            name="email"
            type="email"
            value={form.email}
            onChange={onChange}
            required
          />
        </div>

        <div>
          <label htmlFor="account-password">
            Password
          </label>

          <input
            id="account-password"
            name="password"
            type="password"
            value={form.password}
            onChange={onChange}
            required
            minLength={8}
          />
        </div>

        <div className="form-row">
          <button
            className="btn-primary"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create Account"}
          </button>

          <button
            className="btn-secondary"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}

export default AccountForm;