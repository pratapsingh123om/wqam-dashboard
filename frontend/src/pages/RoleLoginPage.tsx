import { useState } from 'react';
import LoginForm from '../components/LoginForm';
import SignUpForm from '../components/SignUpForm'; // New import

// Define the roles for type safety
type Role = 'Validator' | 'Business' | 'STP/WTP Plant' | 'Admin';

const RoleCard = ({ icon, title, description, onClick }: { icon: string, title: string, description: string, onClick: () => void }) => (
  <div
    className="bg-slate-800 rounded-2xl p-10 cursor-pointer transition-all duration-300 ease-in-out shadow-lg hover:shadow-2xl hover:-translate-y-2 transform-gpu"
    onClick={onClick}
  >
    <div className="text-6xl mb-4 text-center text-blue-400">{icon}</div>
    <h3 className="text-2xl font-bold text-center text-white mb-2">{title}</h3>
    <p className="text-center text-slate-400 text-sm leading-relaxed">{description}</p>
  </div>
);

// Update props to include onRegister and registration-related state
const RoleLoginPage = ({ onLogin, onRegister, loading, loginError, registerLoading, registerError }: {
    onLogin: (credentials: { username: string; password: string }) => void;
    onRegister: (credentials: { username: string; password: string; role: string }) => Promise<void>;
    loading: boolean;
    loginError: string | null;
    registerLoading: boolean;
    registerError: string | null;
}) => {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [showSignUp, setShowSignUp] = useState(false); // New state

  const handleRoleSelect = (role: Role) => {
    setSelectedRole(role);
    setShowSignUp(false); // Ensure we are on login form when role is selected
  };

  const handleBackToRoles = () => {
    setSelectedRole(null);
    setShowSignUp(false);
  };

  const handleShowSignup = () => {
    setShowSignUp(true);
    setSelectedRole(null); // Clear selected role when going to generic signup
  };

  if (showSignUp) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-purple-600 to-blue-600 text-white flex items-center justify-center p-4">
        <SignUpForm
          onSignUp={onRegister}
          loading={registerLoading}
          error={registerError}
          onBack={handleBackToRoles}
        />
      </div>
    );
  }

  if (selectedRole) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-purple-600 to-blue-600 text-white flex items-center justify-center p-4">
        <LoginForm
          role={selectedRole}
          onLogin={onLogin}
          loading={loading}
          error={loginError}
          onBack={handleBackToRoles} // Back to role selection
          onShowSignup={handleShowSignup} // Option to go to signup from login form
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-purple-600 to-blue-600 text-white p-4">
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-3">
            Water Quality Monitoring Dashboard
          </h1>
          <p className="text-lg text-slate-300">
            Please select your role to proceed
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <RoleCard
            icon="✓"
            title="Validator"
            description="Access validation tools and approve water quality reports"
            onClick={() => handleRoleSelect('Validator')}
          />
          <RoleCard
            icon="🏢"
            title="Business/Industry"
            description="Monitor your facility's water quality compliance and reports"
            onClick={() => handleRoleSelect('Business')}
          />
          <RoleCard
            icon="🏭"
            title="STP/WTP Plant"
            description="Manage treatment plant operations and water quality data"
            onClick={() => handleRoleSelect('STP/WTP Plant')}
          />
        </div>

        <div className="text-center mt-16">
          {/* Admin login has been moved to its own page */}
        </div>
      </div>
    </div>
  );
};

export default RoleLoginPage;