#ifndef PREDICATE_H__
#define PREDICATE_H__

#include <memory>
#include <set>
#include <string>
#include "Singleton.hpp"

namespace cclyzer {
    /* Forward declarations to be able to define actual registries */
    class Predicate;

    /* Registry base class */
    template<typename T>
    class Registry
    {
      public:
        Registry() {
            all().insert((const T*)(this));
        }

        // Define iterator methods over class instances

        typedef typename std::set< const T* >::const_iterator iterator;

        static iterator begin() {
            return all().begin();
        }

        static iterator end() {
            return all().end();
        }

      protected:
        ~Registry() {
            all().erase((const T*)(this));
        }

        // Collection of instances
        static std::set< const T* >& all();

      private:
        // Make objects non-copyable
        Registry (const Registry &);
        Registry & operator = (const Registry &);
    };

    template class Registry<Predicate>;
}

/* Predicate */

class cclyzer::Predicate
    : public Registry<Predicate>
{
  public:

    Predicate(const char *name) : name(name) {}
    Predicate(const std::string& name) : name(name) {}

    // Conversions

    std::string getName() const {
        return name;
    }

    operator std::string() const {
        return name;
    }

    const char *c_str() const {
        return name.c_str();
    }


    // Comparison operators

    friend bool operator== (Predicate &p1, Predicate &p2);
    friend bool operator!= (Predicate &p1, Predicate &p2);

    friend bool operator> (Predicate &p1, Predicate &p2);
    friend bool operator<= (Predicate &p1, Predicate &p2);

    friend bool operator< (Predicate &p1, Predicate &p2);
    friend bool operator>= (Predicate &p1, Predicate &p2);

    friend std::ostream& operator<<(std::ostream& stream, const Predicate&p);

    virtual ~Predicate() {}

  private:
    const std::string name;

    Predicate( const Predicate& other ) = delete; // non construction-copyable
    Predicate& operator=( const Predicate& ) = delete; // non copyable
};

#endif
