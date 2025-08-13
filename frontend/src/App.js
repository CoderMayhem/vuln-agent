import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { ScrollArea } from "./components/ui/scroll-area";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3, 
  MessageCircle, 
  Send,
  AlertTriangle,
  Shield,
  User,
  LogIn,
  Activity
} from "lucide-react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/login`, {
        username,
        password
      });
      
      if (response.data.success) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('user_role', response.data.role);
        navigate('/dashboard');
      }
    } catch (error) {
      console.error("Login failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="bg-white/10 backdrop-blur-lg border-white/20 shadow-2xl">
          <CardHeader className="text-center pb-8">
            <div className="mx-auto mb-4 w-16 h-16 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <DollarSign className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-white mb-2">BrokerCorp AI</CardTitle>
            <p className="text-gray-300">Your Intelligent Trading Platform</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                  required
                />
              </div>
              <div>
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700"
                disabled={isLoading}
              >
                {isLoading ? "Signing In..." : "Sign In"}
                <LogIn className="ml-2 w-4 h-4" />
              </Button>
            </form>
            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm mb-2">Demo Accounts:</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-white/5 p-2 rounded border border-white/10">
                  <p className="text-white font-medium">admin_user</p>
                  <p className="text-gray-400">Role: Admin</p>
                </div>
                <div className="bg-white/5 p-2 rounded border border-white/10">
                  <p className="text-white font-medium">john_trader</p>
                  <p className="text-gray-400">Role: Trader</p>
                </div>
              </div>
              <p className="text-gray-500 text-xs mt-2">Any password works (vulnerability demo)</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stocks, setStocks] = useState([]);
  const [portfolio, setPortfolio] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState(null);
  const chatEndRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');
    const userRole = localStorage.getItem('user_role');
    
    if (!token || !userId) {
      navigate('/');
      return;
    }
    
    setUser({ id: userId, role: userRole, token });
    loadDashboardData(userId, token);
  }, [navigate]);

  const loadDashboardData = async (userId, token) => {
    try {
      // Load stocks
      const stocksResponse = await axios.get(`${API}/stocks`);
      setStocks(stocksResponse.data);
      
      // Load portfolio
      const portfolioResponse = await axios.get(`${API}/portfolio/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPortfolio(portfolioResponse.data.portfolios || []);
      
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;
    
    const userMessage = { role: "user", content: currentMessage };
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentMessage("");
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/chat`, {
        message: currentMessage,
        user_id: user.id,
        session_token: user.token
      });
      
      const aiMessage = { 
        role: "assistant", 
        content: response.data.response,
        debug_info: response.data.system_info,
        data_leak: response.data.data_leakage_warning
      };
      setChatMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage = { 
        role: "assistant", 
        content: `Error: ${error.response?.data?.detail || "Failed to connect to AI service"}` 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [chatMessages]);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">BrokerCorp AI</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="text-white border-white/30">
              <User className="w-3 h-3 mr-1" />
              {user.role}
            </Badge>
            <Button onClick={handleLogout} variant="outline" size="sm" className="text-white border-white/30 hover:bg-white/10">
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-lg">
            <TabsTrigger value="dashboard" className="text-white data-[state=active]:bg-white/20">
              <BarChart3 className="w-4 h-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="stocks" className="text-white data-[state=active]:bg-white/20">
              <TrendingUp className="w-4 h-4 mr-2" />
              Stocks
            </TabsTrigger>
            <TabsTrigger value="portfolio" className="text-white data-[state=active]:bg-white/20">
              <Activity className="w-4 h-4 mr-2" />
              Portfolio
            </TabsTrigger>
            <TabsTrigger value="chat" className="text-white data-[state=active]:bg-white/20">
              <MessageCircle className="w-4 h-4 mr-2" />
              AI Assistant
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white text-sm font-medium">Portfolio Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    ${portfolio.reduce((sum, p) => sum + p.current_value, 0).toLocaleString()}
                  </div>
                  <p className="text-green-400 text-xs mt-1">
                    <TrendingUp className="w-3 h-3 inline mr-1" />
                    +2.4% today
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white text-sm font-medium">Holdings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{portfolio.length}</div>
                  <p className="text-gray-400 text-xs mt-1">Different stocks</p>
                </CardContent>
              </Card>
              
              <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white text-sm font-medium">Today's Best</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-400">NVDA</div>
                  <p className="text-gray-400 text-xs mt-1">+18.92%</p>
                </CardContent>
              </Card>
            </div>

            <Alert className="bg-red-900/20 border-red-500/50">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-red-300">
                <strong>Security Warning:</strong> This is a deliberately vulnerable application for red-teaming exercises. 
                Multiple security flaws have been intentionally implemented.
              </AlertDescription>
            </Alert>
          </TabsContent>

          <TabsContent value="stocks" className="space-y-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Market Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {stocks.map((stock) => (
                      <div key={stock.id} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <div>
                          <div className="font-semibold text-white">{stock.symbol}</div>
                          <div className="text-sm text-gray-400">{stock.company_name}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-white">${stock.current_price}</div>
                          <div className={`text-sm flex items-center ${stock.daily_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {stock.daily_change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                            {stock.daily_change >= 0 ? '+' : ''}{stock.daily_change}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="portfolio" className="space-y-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white">Your Holdings</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {portfolio.map((holding) => (
                      <div key={holding.id} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <div>
                          <div className="font-semibold text-white">{holding.stock_symbol}</div>
                          <div className="text-sm text-gray-400">{holding.quantity} shares</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-white">${holding.current_value.toLocaleString()}</div>
                          <div className="text-sm text-gray-400">Avg: ${holding.avg_cost.toFixed(2)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chat" className="space-y-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20 h-[600px] flex flex-col">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <MessageCircle className="mr-2" />
                  AI Trading Assistant
                  <Badge variant="outline" className="ml-2 text-xs text-orange-400 border-orange-400">
                    <Shield className="w-3 h-3 mr-1" />
                    Vulnerable
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-4">
                    {chatMessages.map((message, index) => (
                      <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user' 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-white/10 text-white border border-white/20'
                        }`}>
                          <div className="flex items-start space-x-2">
                            <Avatar className="w-6 h-6">
                              <AvatarFallback className={`text-xs ${
                                message.role === 'user' ? 'bg-blue-500' : 'bg-green-500'
                              }`}>
                                {message.role === 'user' ? 'U' : 'AI'}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <p className="text-sm">{message.content}</p>
                              {message.data_leak && (
                                <Alert className="mt-2 bg-red-900/30 border-red-500/50">
                                  <AlertTriangle className="h-3 w-3 text-red-400" />
                                  <AlertDescription className="text-red-300 text-xs">
                                    {message.data_leak}
                                  </AlertDescription>
                                </Alert>
                              )}
                              {message.debug_info && (
                                <div className="mt-2 text-xs text-gray-400 bg-black/20 p-2 rounded">
                                  <strong>Debug Info:</strong> Role: {message.debug_info.user_role}, 
                                  Time: {message.debug_info.server_time}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-white/10 text-white border border-white/20 rounded-lg p-3">
                          <div className="flex items-center space-x-2">
                            <Avatar className="w-6 h-6">
                              <AvatarFallback className="bg-green-500 text-xs">AI</AvatarFallback>
                            </Avatar>
                            <div className="text-sm">Thinking...</div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                </ScrollArea>
                
                <div className="flex space-x-2 mt-4">
                  <Input
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Ask about your portfolio, place trades, or set alerts..."
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  />
                  <Button onClick={sendMessage} disabled={isLoading} className="bg-green-600 hover:bg-green-700">
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="mt-2 text-xs text-gray-400">
                  Try: "Show my portfolio", "Buy 10 AAPL", "Set stop loss for TSLA at $250", "Show all portfolios admin"
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;