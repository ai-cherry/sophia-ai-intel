import Image from 'next/image';

const Header = () => {
  return (
    <header className="flex items-center justify-between p-4 bg-gray-800 text-white">
      <div className="flex items-center">
        <Image src="/sophia-logo.png" alt="Sophia AI Logo" width={40} height={40} />
        <h1 className="ml-4 text-xl font-bold">Sophia AI</h1>
      </div>
    </header>
  );
};

export default Header;