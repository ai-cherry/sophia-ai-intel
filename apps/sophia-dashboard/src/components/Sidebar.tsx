import Link from 'next/link';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white p-4">
      <nav>
        <ul>
          <li className="mb-2">
            <Link href="/" className="block p-2 rounded hover:bg-gray-700">
              Dashboard
            </Link>
          </li>
          <li className="mb-2">
            <Link href="/chat" className="block p-2 rounded hover:bg-gray-700">
              Chat
            </Link>
          </li>
          <li className="mb-2">
            <Link href="/agent-factory" className="block p-2 rounded hover:bg-gray-700">
              Agent Factory
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;