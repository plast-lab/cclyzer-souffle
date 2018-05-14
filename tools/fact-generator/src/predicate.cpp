#include "predicate.hpp"

// Add to current namespace
using cclyzer::Registry;
using cclyzer::Predicate;

// Initialize registries
template <typename T> std::set< const T* >& Registry<T>::all() {
    static std::set< const T* > *allInstances = new std::set< const T*>();
    return *allInstances;
}

// Add explicit instantiations
namespace cclyzer {
    template std::set< const Predicate* >& Registry<Predicate>::all();
}

// Comparing predicates

namespace cclyzer {

    bool operator== (Predicate &p1, Predicate &p2) {
        return p1.name == p2.name;
    }

    bool operator!= (Predicate &p1, Predicate &p2) {
        return p1.name != p2.name;
    }

    bool operator< (Predicate &p1, Predicate &p2) {
        return p1.name < p2.name;
    }

    bool operator<= (Predicate &p1, Predicate &p2) {
        return p1.name <= p2.name;
    }

    bool operator> (Predicate &p1, Predicate &p2) {
        return p1.name > p2.name;
    }

    bool operator>= (Predicate &p1, Predicate &p2) {
        return p1.name >= p2.name;
    }

    std::ostream& operator<<(std::ostream& stream, const Predicate& pred) {
        return stream << std::string(pred);
    }
}
